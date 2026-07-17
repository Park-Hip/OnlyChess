"""Tests for the simple event registry."""

import unittest

from src.events import create_event, get_registered_event_keys
from src.events.comeout import Comeout
from src.events.gia_xang_tang import GiaXangTang
from src.events.kho_ga_tron_ba_mia import KhoGaTronBaMia
from src.events.long_toi_tan_nat_khi_nhan_ra_toi_la_gay import LongToiTanNatKhiNhanRaToiLaGay
from src.events.mat_quyen_cong_dan import MatQuyenCongDan
from src.events.my_danh_iran import MyDanhIran
from src.events.nguoi_chong_bat_luc import NguoiChongBatLuc
from src.events.tai_xiu import TaiXiu
from src.events.umamusume import Umamusume
from src.events.viec_nhe_vol_cao import ViecNheVolCao
from src.events.registry import get_event_class
from src.game.board import GameState


class EventRegistryTests(unittest.TestCase):
    """Verify event lookup and construction are registry-driven."""

    def test_registered_event_keys_include_gia_xang_tang(self):
        self.assertIn("gia_xang_tang", get_registered_event_keys())
        self.assertIn("comeout", get_registered_event_keys())
        self.assertIn("tai_xiu", get_registered_event_keys())
        self.assertIn("umamusume", get_registered_event_keys())
        self.assertIn("long_toi_tan_nat_khi_nhan_ra_toi_la_gay", get_registered_event_keys())
        self.assertIn("mat_quyen_cong_dan", get_registered_event_keys())
        self.assertIn("my_danh_iran", get_registered_event_keys())
        self.assertIn("viec_nhe_vol_cao", get_registered_event_keys())
        self.assertIn("nguoi_chong_bat_luc", get_registered_event_keys())
        self.assertIn("kho_ga_tron_ba_mia", get_registered_event_keys())

    def test_get_event_class_returns_registered_class(self):
        self.assertIs(get_event_class("gia_xang_tang"), GiaXangTang)
        self.assertIs(get_event_class("comeout"), Comeout)
        self.assertIs(get_event_class("tai_xiu"), TaiXiu)
        self.assertIs(get_event_class("umamusume"), Umamusume)
        self.assertIs(
            get_event_class("long_toi_tan_nat_khi_nhan_ra_toi_la_gay"),
            LongToiTanNatKhiNhanRaToiLaGay,
        )
        self.assertIs(get_event_class("mat_quyen_cong_dan"), MatQuyenCongDan)
        self.assertIs(get_event_class("my_danh_iran"), MyDanhIran)
        self.assertIs(get_event_class("viec_nhe_vol_cao"), ViecNheVolCao)
        self.assertIs(get_event_class("nguoi_chong_bat_luc"), NguoiChongBatLuc)
        self.assertIs(get_event_class("kho_ga_tron_ba_mia"), KhoGaTronBaMia)

    def test_create_event_builds_event_from_key(self):
        event = create_event("gia_xang_tang", GameState())
        second_event = create_event("comeout", GameState())
        third_event = create_event("tai_xiu", GameState())
        fourth_event = create_event("umamusume", GameState())
        fifth_event = create_event("long_toi_tan_nat_khi_nhan_ra_toi_la_gay", GameState())
        sixth_event = create_event("mat_quyen_cong_dan", GameState())
        seventh_event = create_event("my_danh_iran", GameState())
        eighth_event = create_event("viec_nhe_vol_cao", GameState())
        ninth_event = create_event("nguoi_chong_bat_luc", GameState())
        tenth_event = create_event("kho_ga_tron_ba_mia", GameState())

        self.assertIsInstance(event, GiaXangTang)
        self.assertEqual(event.event_key, "gia_xang_tang")
        self.assertIsInstance(second_event, Comeout)
        self.assertEqual(second_event.event_key, "comeout")
        self.assertIsInstance(third_event, TaiXiu)
        self.assertEqual(third_event.event_key, "tai_xiu")
        self.assertIsInstance(fourth_event, Umamusume)
        self.assertEqual(fourth_event.event_key, "umamusume")
        self.assertIsInstance(fifth_event, LongToiTanNatKhiNhanRaToiLaGay)
        self.assertEqual(fifth_event.event_key, "long_toi_tan_nat_khi_nhan_ra_toi_la_gay")
        self.assertIsInstance(sixth_event, MatQuyenCongDan)
        self.assertEqual(sixth_event.event_key, "mat_quyen_cong_dan")
        self.assertIsInstance(seventh_event, MyDanhIran)
        self.assertEqual(seventh_event.event_key, "my_danh_iran")
        self.assertIsInstance(eighth_event, ViecNheVolCao)
        self.assertEqual(eighth_event.event_key, "viec_nhe_vol_cao")
        self.assertIsInstance(ninth_event, NguoiChongBatLuc)
        self.assertEqual(ninth_event.event_key, "nguoi_chong_bat_luc")
        self.assertIsInstance(tenth_event, KhoGaTronBaMia)
        self.assertEqual(tenth_event.event_key, "kho_ga_tron_ba_mia")


if __name__ == "__main__":
    unittest.main()
