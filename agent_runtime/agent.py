# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext

# from google.adk.tools.load_memory_tool import LoadMemoryTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


def get_weather(city: str) -> dict:
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25 degrees Celsius (77 degrees Fahrenheit).",
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }


def get_current_time(city: str) -> dict:
    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have timezone information for {city}.",
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f"The current time in {city} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
    return {"status": "success", "report": report}


# # https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart#manage-memories
# async def add_session_to_memory_callback(callback_context: CallbackContext):
#     await callback_context.add_session_to_memory()
#     return None


# https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart?hl=ko#memory-generation-callback
async def generate_memories_callback(callback_context: CallbackContext):
    # Option 1 (Recommended): Send events to Memory Bank for memory generation,
    # which is ideal for incremental processing of events.
    await callback_context.add_events_to_memory(
        events=callback_context.session.events[-5:-1]
    )

    # Option 2: Send the full session to Memory Bank for memory generation.
    # It's recommended to only call this at the end of a session to minimize
    # how many times a single event is re-processed.
    # await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    name="weather_time_agent",
    model="gemini-3.5-flash",
    description="Agent to answer questions about the time and weather in a city.",
    instruction="You are a helpful agent who can answer user questions about the time and weather in a city.",
    after_agent_callback=generate_memories_callback,
    # https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/adk-quickstart?hl=ko#define_a_memory_retrieval_tool
    tools=[get_weather, get_current_time, PreloadMemoryTool()],
)
