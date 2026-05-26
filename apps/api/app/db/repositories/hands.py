from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping, desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import actions, hand_players, hands, pots
from app.parser.models import HandDraft


class HandsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_many(
        self,
        user_id: UUID,
        import_id: UUID,
        drafts: list[HandDraft],
        chunk_size: int = 1000,
    ) -> int:
        inserted = 0
        for offset in range(0, len(drafts), chunk_size):
            for draft in drafts[offset : offset + chunk_size]:
                if await self._insert_one(user_id, import_id, draft):
                    inserted += 1
        return inserted

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> list[RowMapping]:
        result = await self.session.execute(
            select(hands)
            .where(hands.c.user_id == user_id)
            .order_by(desc(hands.c.played_at))
            .limit(limit)
        )
        return list(result.mappings().all())

    async def get_for_user(self, user_id: UUID, hand_id: UUID) -> RowMapping | None:
        result = await self.session.execute(
            select(hands).where(hands.c.user_id == user_id, hands.c.id == hand_id)
        )
        return result.mappings().one_or_none()

    async def get_detail_for_user(self, user_id: UUID, hand_id: UUID) -> dict[str, Any] | None:
        hand = await self.get_for_user(user_id, hand_id)
        if hand is None:
            return None
        seats_result = await self.session.execute(
            select(hand_players)
            .where(hand_players.c.hand_id == hand_id)
            .order_by(hand_players.c.seat)
        )
        actions_result = await self.session.execute(
            select(actions).where(actions.c.hand_id == hand_id).order_by(actions.c.sequence)
        )
        pots_result = await self.session.execute(
            select(pots).where(pots.c.hand_id == hand_id).order_by(pots.c.pot_index)
        )
        return {
            "hand": hand,
            "seats": list(seats_result.mappings().all()),
            "actions": list(actions_result.mappings().all()),
            "pots": list(pots_result.mappings().all()),
        }

    async def _insert_one(self, user_id: UUID, import_id: UUID, draft: HandDraft) -> bool:
        result = await self.session.execute(
            insert(hands)
            .values(
                user_id=user_id,
                import_id=import_id,
                site=draft.site,
                site_hand_id=draft.site_hand_id,
                site_tournament_id=draft.site_tournament_id,
                site_table_name=draft.site_table_name,
                game_type=draft.game_type,
                variant=draft.variant,
                table_max_players=draft.table_max_players,
                buy_in_cents=draft.buy_in_cents,
                fee_cents=draft.fee_cents,
                currency=draft.currency,
                level_name=draft.level_name,
                small_blind=draft.small_blind,
                big_blind=draft.big_blind,
                ante=draft.ante,
                button_seat=draft.button_seat,
                hero_seat=draft.hero_seat,
                hero_username=draft.hero_username,
                played_at=draft.played_at,
                timezone_at_play=draft.timezone_at_play,
                board_cards=draft.board,
                pot_total=draft.pot_total,
                rake=draft.rake,
                hero_position=draft.hero_position,
                hero_starting_stack=draft.hero_starting_stack,
                hero_hole_cards=draft.hero_hole_cards,
                hero_net_cents=draft.hero_net_cents,
                hero_went_to_showdown=draft.hero_went_to_showdown,
                hero_won_at_showdown=draft.hero_won_at_showdown,
                h_saw_flop=draft.h_saw_flop,
                h_saw_turn=draft.h_saw_turn,
                h_saw_river=draft.h_saw_river,
                h_went_to_sd=draft.hero_went_to_showdown,
                h_won_at_sd=bool(draft.hero_won_at_showdown),
                h_vpip=draft.h_vpip,
                h_pfr=draft.h_pfr,
                h_three_bet=draft.h_three_bet,
                h_faced_three_bet=draft.h_faced_three_bet,
                h_folded_to_three_bet=draft.h_folded_to_three_bet,
                h_pf_open=draft.h_pf_open,
                h_postflop_bets=draft.h_postflop_bets,
                h_postflop_raises=draft.h_postflop_raises,
                h_postflop_calls=draft.h_postflop_calls,
                raw_text=draft.raw_text,
                parser_version=draft.parser_version,
            )
            .on_conflict_do_nothing(index_elements=["user_id", "site", "site_hand_id"])
            .returning(hands.c.id)
        )
        hand_id = result.scalar_one_or_none()
        if hand_id is None:
            return False
        player_ids: dict[str, UUID] = {}
        for seat in draft.seats:
            player_result = await self.session.execute(
                insert(hand_players)
                .values(
                    hand_id=hand_id,
                    seat=seat.seat,
                    username=seat.username,
                    starting_stack=seat.starting_stack,
                    position=seat.position,
                    is_hero=seat.is_hero,
                    sit_out=seat.sit_out,
                    posted_blind=seat.posted_blind,
                    blind_amount=seat.blind_amount,
                    hole_cards=seat.hole_cards,
                    went_to_showdown=seat.went_to_showdown,
                    won_amount=seat.won_amount,
                    final_action_street=seat.final_action_street,
                )
                .returning(hand_players.c.id)
            )
            player_ids[seat.username] = player_result.scalar_one()
        if draft.actions:
            await self.session.execute(
                insert(actions),
                [
                    {
                        "hand_id": hand_id,
                        "user_id": user_id,
                        "player_id": player_ids[action.player_name],
                        "sequence": action.sequence,
                        "street": action.street,
                        "action_type": action.action_type,
                        "amount": action.amount,
                        "raise_to": action.raise_to,
                        "is_all_in": action.is_all_in,
                        "pot_before": action.pot_before,
                        "pot_after": action.pot_after,
                    }
                    for action in draft.actions
                    if action.player_name in player_ids
                ],
            )
        if draft.pots:
            await self.session.execute(
                insert(pots),
                [
                    {
                        "hand_id": hand_id,
                        "pot_index": pot.pot_index,
                        "amount": pot.amount,
                        "rake": pot.rake,
                        "winners": [
                            player_ids[name] for name in pot.winner_names if name in player_ids
                        ],
                    }
                    for pot in draft.pots
                ],
            )
        return True
