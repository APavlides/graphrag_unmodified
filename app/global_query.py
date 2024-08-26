import os
import pandas as pd
import tiktoken

from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_reports
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch
import streamlit as st

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


async def execute_global_query(question: str, mock=True):

    if mock:
        result = {
            "response": """## Summary of Treatment Received by John Doe

                            John Doe has undergone a comprehensive treatment plan aimed at managing his anxiety and depression. A significant component of his therapy has been Cognitive Behavioral Therapy (CBT), which focuses on altering negative thought patterns to improve his mental health [Data: Reports (1, 0, +more)].

                            ### Ongoing Support

                            To ensure continuous support, John has been scheduled for weekly therapy sessions. These sessions are crucial for monitoring his mental health and fostering a sense of stability in his life [Data: Reports (0, +more)].

                            ### Family and Academic Support"""
        }

    else:
        api_key = os.environ["GRAPHRAG_API_KEY"]
        llm_model = os.environ["GRAPHRAG_LLM_MODEL"]
        # api_key = st.secrets["GRAPHRAG_API_KEY"]
        # llm_model = st.secrets["GRAPHRAG_LLM_MODEL"]

        llm = ChatOpenAI(
            api_key=api_key,
            model=llm_model,
            api_type=OpenaiApiType.AzureOpenAI,  # OpenaiApiType.OpenAI or OpenaiApiType.OpenAI
            api_base="https://theraflow-openai.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-02-15-preview",
            api_version="2024-02-15-preview",
            max_retries=20,
        )

        token_encoder = tiktoken.get_encoding("cl100k_base")

        # parquet files generated from indexing pipeline
        INPUT_DIR = "./output/20240825-115048/artifacts"
        COMMUNITY_REPORT_TABLE = "create_final_community_reports"
        ENTITY_TABLE = "create_final_nodes"
        ENTITY_EMBEDDING_TABLE = "create_final_entities"

        # community level in the Leiden community hierarchy from which we will load the community reports
        # higher value means we use reports from more fine-grained communities (at the cost of higher computation cost)
        COMMUNITY_LEVEL = 2

        entity_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_TABLE}.parquet")
        report_df = pd.read_parquet(f"{INPUT_DIR}/{COMMUNITY_REPORT_TABLE}.parquet")
        entity_embedding_df = pd.read_parquet(
            f"{INPUT_DIR}/{ENTITY_EMBEDDING_TABLE}.parquet"
        )

        reports = read_indexer_reports(report_df, entity_df, COMMUNITY_LEVEL)
        entities = read_indexer_entities(
            entity_df, entity_embedding_df, COMMUNITY_LEVEL
        )
        print(f"Total report count: {len(report_df)}")
        print(
            f"Report count after filtering by community level {COMMUNITY_LEVEL}: {len(reports)}"
        )
        report_df.head()

        context_builder = GlobalCommunityContext(
            community_reports=reports,
            entities=entities,  # default to None if you don't want to use community weights for ranking
            token_encoder=token_encoder,
        )

        context_builder_params = {
            "use_community_summary": False,  # False means using full community reports. True means using community short summaries.
            "shuffle_data": True,
            "include_community_rank": True,
            "min_community_rank": 0,
            "community_rank_name": "rank",
            "include_community_weight": True,
            "community_weight_name": "occurrence weight",
            "normalize_community_weight": True,
            "max_tokens": 12_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
            "context_name": "Reports",
        }

        map_llm_params = {
            "max_tokens": 1000,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        reduce_llm_params = {
            "max_tokens": 2000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000-1500)
            "temperature": 0.0,
        }

        search_engine = GlobalSearch(
            llm=llm,
            context_builder=context_builder,
            token_encoder=token_encoder,
            max_data_tokens=12_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
            map_llm_params=map_llm_params,
            reduce_llm_params=reduce_llm_params,
            allow_general_knowledge=False,  # set this to True will add instruction to encourage the LLM to incorporate general knowledge in the response, which may increase hallucinations, but could be useful in some use cases.
            json_mode=True,  # set this to False if your LLM model does not support JSON mode.
            context_builder_params=context_builder_params,
            concurrent_coroutines=32,
            response_type="single paragraph per question",  # free form text describing the response type and format, can be anything, e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
        )

        result = await search_engine.asearch(question)

    return result

    # print(result.response)

    # # inspect the data used to build the context for the LLM responses
    # print(result.context_data["reports"])

    # # inspect number of LLM calls and tokens
    # print(f"LLM calls: {result.llm_calls}. LLM tokens: {result.prompt_tokens}")


# Run the async main function
# import asyncio
# result = asyncio.run(main(question="Provide a short summary of the treatment this patient has received in the past.", mock=True))
# print(result)

if __name__ == "__main__":
    import argparse
    import asyncio

    # Define the parser
    parser = argparse.ArgumentParser(description="run a global query")

    # Declare an argument (`--algo`), saying that the
    # corresponding value should be stored in the `algo`
    # field, and using a default value if the argument
    # isn't given
    parser.add_argument(
        "--question",
        action="store",
        dest="question",
        default="What is the patient's name?",
    )

    # Now, parse the command line arguments and store the
    # values in the `args` variable
    args = parser.parse_args()
    print(args.question)
    result = asyncio.run(execute_global_query(question=args.question, mock=False))
    print(result.response)
