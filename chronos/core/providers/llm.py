from typing import Dict

from dishka import Provider, Scope, provide
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI

from chronos.core.settings import Settings
from chronos.schemas.enums.providers import LLMProvider


class LLMAdaptersProvider(Provider):
    @provide(scope=Scope.APP)
    def llm_providers(
        self,
        chat_openai: ChatOpenAI,
        chat_anthropic: ChatAnthropic,
    ) -> Dict[LLMProvider, BaseLanguageModel]:
        return {
            LLMProvider.OPENAI: chat_openai,
            LLMProvider.ANTHROPIC: chat_anthropic,
        }

    @provide(scope=Scope.APP)
    def chat_openai(self, settings: Settings) -> ChatOpenAI:
        assert settings.openai_api_key, "OpenAI API key is not configured"
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_retries=settings.openai_max_retries,
        )

    @provide(scope=Scope.APP)
    def chat_anthropic(self, settings: Settings) -> ChatAnthropic:
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model_name=settings.anthropic_model,
            model=settings.anthropic_model,
            temperature=settings.anthropic_temperature,
            max_retries=settings.anthropic_max_retries,
            timeout=None,
            stop=None,
        )
