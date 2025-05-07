from enum import Enum
from typing import Dict, List, Self, Tuple, Type, cast

from chronos.services.crawlers.base import BaseCrawler
from chronos.services.crawlers.tiktok.affiliate import TiktokAffiliateCrawler
from chronos.services.crawlers.tiktok.newsfeed import TiktokNewsfeedCrawler
from chronos.services.crawlers.tiktok.search import TiktokSearchCrawler


class Platform(Enum):
    TIKTOK_AFFILIATE = {
        "crawler": TiktokAffiliateCrawler,
        "configs": {
            "login_url": "https://seller-vn.tiktok.com/account/login?redirect_url={redirect_url}",
            "search_url": "https://affiliate.tiktok.com/connection/creator?shop_region=VN",
            "creator_detail_url": "https://affiliate.tiktok.com/connection/creator/detail?{params}",
            "email_panel_selector": "#TikTok_Ads_SSO_Login_Email_Panel_Button",
            "email_input_selector": "#TikTok_Ads_SSO_Login_Email_Input",
            "pwd_input_selector": "#TikTok_Ads_SSO_Login_Pwd_Input",
            "otp_input_selector": "#TikTok_Ads_SSO_Login_Code_Input",
            "search_input_selector": "input[data-tid='m4b_input_search']",
            "creator_span_selector": "span[data-e2e='fbc99397-6043-1b37']:text('{creator_id}')",
        },
    }

    TIKTOK_SEARCH = {
        "crawler": TiktokSearchCrawler,
        "configs": {
            "search_url": "https://www.tiktok.com/search",
        },
    }

    TIKTOK_NEWSFEED = {
        "crawler": TiktokNewsfeedCrawler,
        "configs": {
            "newsfeed_url": "https://www.tiktok.com/",
        },
    }

    @property
    def crawler(self) -> Type[BaseCrawler]:
        assert "crawler" in self.value, f"Platform {self} does not have a crawler class"
        return cast(Type[BaseCrawler], self.value["crawler"])

    @property
    def configs(self) -> "PlatformConfig":
        assert "configs" in self.value, f"Platform {self} does not have configs"
        assert isinstance(self.value["configs"], dict), f"Platform {self} configs is not a dict"
        raw_config = cast(Dict[str, str], self.value["configs"])
        return PlatformConfig(config=raw_config)

    @classmethod
    def from_str(cls, key: str) -> Self:
        try:
            return cls[key]
        except ValueError:
            msg = f"Unsupported platform: {key}. Supported platforms are: {[platform.name for platform in cls]}"
            raise ValueError(msg)


class PlatformConfig:
    def __init__(self, config: Dict[str, str]) -> None:
        self._config = config

    def __getattr__(self, key: str) -> str:
        if key not in self._config:
            msg = f"Config key '{key}' not found in platform '{self._config}'"
            raise AttributeError(msg)

        return self._config[key]

    def __getitem__(self, key: str) -> str:
        return self.__getattr__(key)

    def __contains__(self, key: str) -> bool:
        return key in self._config

    def __repr__(self) -> str:
        return repr(self._config)

    def keys(self) -> List[str]:
        return cast(List[str], self._config.keys())

    def values(self) -> List[str]:
        return cast(List[str], self._config.values())

    def items(self) -> List[Tuple[str, str]]:
        return cast(List[Tuple[str, str]], self._config.items())
