#test to confirm all the bugfixes are inplace and ok
import json
from dotenv import load_dotenv
import pytest
import os
from pathlib import Path
from typing import Callable, Any, Dict

from just_agents.data_classes import Message, Role
from just_agents.protocols.sse_streaming import ServerSentEventsStream as SSE
from just_agents.base_agent import BaseAgent, BaseAgentWithLogging
from just_agents.web.web_agent import WebAgent
from just_agents.just_tool import JustToolsBus
from just_agents.web.chat_ui_agent import ChatUIAgent
from just_agents.web.streaming import response_from_stream

TESTS_DIR = os.path.dirname(__file__)  # Get the directory where this test file is located
MODELS_DIR = os.path.join(TESTS_DIR, "models.d")  # Path to models.d inside tests

@pytest.fixture(scope="module", autouse=True)
def load_env():
    load_dotenv(override=True)

def load_agents(load_env,tmp_path) -> Dict[str,BaseAgent]:
    config_path = Path(TESTS_DIR) / "profiles" / "problematic_configs.yaml"
    os.environ["TMP_DIR"] = str(tmp_path)
    agents : dict[str,BaseAgent] = WebAgent.from_yaml_dict(yaml_path=config_path, required_base_class=WebAgent )
    return agents

def test_agents_loaded(load_env,tmp_path):
    agents = load_agents(load_env,tmp_path)
    assert agents
   # assert len(agents.keys()) == 7
    assert "groq_agent" in agents
    assert "openai_agent" in agents
    assert "deepseek_agent" in agents
    assert "deepseek_distilled_agent" in agents
    assert "custom_agent" in agents
    assert "learnLM_agent" in agents
    assert "gemini_agent" in agents


@pytest.mark.skip(reason="expensive and long, run manually")
def test_deepseek_reasoner_agent(load_env,tmp_path):
    agents = load_agents(load_env,tmp_path)
    assert agents
    assert "deepseek_agent" in agents
    assert agents["deepseek_agent"].llm_options["model"] == "deepseek/deepseek-reasoner"
    response = agents["deepseek_agent"].query("Count the number of letters e in deepseek/deepseek-reasoner", send_system_prompt=False)
    assert response
    assert "ten" in response or "10" in response
    response = agents["deepseek_agent"].query("Count the number of letters r in 'strawberry crumble'", send_system_prompt=False)
    assert "four" in response or "4" in response

@pytest.mark.skip(reason="needs server part in test, todo")
def test_custom_agent_config(load_env,tmp_path):
    agents = load_agents(load_env,tmp_path)
    assert agents
    assert "custom_agent" in agents
    #assert agents["custom_agent"].llm_options["custom_llm_provider"] == "openai"
    assert agents["custom_agent"].llm_options["model"] == "sugar_genie"
    assert agents["custom_agent"].llm_options["api_base"] == "http://127.0.0.1:8089/v1"
    response = agents["custom_agent"].query("Who are the founders of GlucoseDao??", send_system_prompt=False)
    assert response

@pytest.mark.skip(reason="https://github.com/BerriAI/litellm/issues/9296")
def test_empty_resp(load_env, tmp_path):
    config_path = Path(TESTS_DIR) / "profiles" / "tool_problem.yaml"
    agent_empty: WebAgent = ChatUIAgent.from_yaml(file_path=config_path, section_name="sugar_genie_empty_response",
                                              parent_section="agent_profiles")
    messages=[Message(
        role=Role.user,
        content="Who are the founders of GlucoseDao??"
    )]
    agent_empty.litellm_tool_description = True
    agent_empty.debug_enabled = True
    stream_generator = agent_empty.stream(
        messages
    )

    response_content = response_from_stream(stream_generator)
    assert response_content #stop with 0 chinks 70% of the time
