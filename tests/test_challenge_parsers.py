import unittest

from tg_signer.challenge_parsers import (
    clean_captcha_ocr_text,
    parse_ordered_button_challenge,
)


BUTTONS = ["🖥️", "🐇", "👑", "1", "👘", "✈️", "🙂", "🔮", "🥕"]


class ChallengeParserTests(unittest.TestCase):
    def test_parse_left_to_right_ordered_button_challenge(self):
        challenge = parse_ordered_button_challenge(
            "🤖 人机验证\n请按照下面目标序列从左到右依次点击：\n👑 ✈ 👘 1 🙂",
            BUTTONS,
        )

        self.assertIsNotNone(challenge)
        self.assertEqual(challenge.direction, "left_to_right")
        self.assertEqual(challenge.targets, ("👑", "✈️", "👘", "1", "🙂"))

    def test_parse_right_to_left_reverses_visual_order(self):
        challenge = parse_ordered_button_challenge(
            "请按照下面目标序列从右往左依次点击：\n👑 ✈️ 👘 1 🙂",
            BUTTONS,
        )

        self.assertIsNotNone(challenge)
        self.assertEqual(challenge.direction, "right_to_left")
        self.assertEqual(challenge.targets, ("🙂", "1", "👘", "✈️", "👑"))

    def test_parse_requires_explicit_direction(self):
        self.assertIsNone(
            parse_ordered_button_challenge("请依次点击：👑 ✈️", BUTTONS)
        )

    def test_clean_captcha_ocr_text_removes_spaces_and_explanation(self):
        self.assertEqual(clean_captcha_ocr_text("Gk GX"), "GkGX")
        self.assertEqual(clean_captcha_ocr_text("验证码是： Gk GX"), "GkGX")
        self.assertEqual(clean_captcha_ocr_text("```text\npf b A\n```"), "pfbA")


if __name__ == "__main__":
    unittest.main()
