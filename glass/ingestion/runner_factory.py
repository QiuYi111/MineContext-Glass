from __future__ import annotations

from typing import Any

from loguru import logger

from opencontext.config.global_config import GlobalConfig

from .auc_runner import AUCTurboConfig, AUCTurboRunner
from .speech_to_text import SpeechToTextRunner
from .whisperx_runner import WhisperXRunner


def build_speech_to_text_runner_from_config() -> SpeechToTextRunner:
    """
    Construct a speech-to-text runner based on the loaded configuration.

    Falls back to WhisperX if the configuration is missing, invalid, or the
    remote runner cannot be initialised.
    """

    stt_config = _load_speech_config()
    provider = (stt_config.get("provider") or "whisperx").lower()

    if provider == "auc_turbo":
        try:
            auc_config = AUCTurboConfig.from_dict(stt_config.get("auc_turbo"))
            return AUCTurboRunner(config=auc_config)
        except Exception as exc:  # noqa: BLE001 - want the exact reason in logs
            logger.warning("Failed to initialise AUC Turbo runner: {}", exc)
            logger.warning("Falling back to WhisperX.")

    return WhisperXRunner()


def _load_speech_config() -> dict[str, Any]:
    try:
        global_config = GlobalConfig.get_instance()
        glass_config = global_config.get_config("glass") or {}
        return glass_config.get("speech_to_text") or {}
    except Exception as exc:  # noqa: BLE001
        logger.debug("Glass speech-to-text config unavailable: {}", exc)
        return {}
