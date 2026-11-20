import os
import boto3

class BedrockService:
    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv(
                "AWS_REGION",
                "ap-northeast-2"
            )
        )

        self.model_id = os.environ["BEDROCK_MODEL_ID"]

    def generate(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        response = self.client.converse(
            modelId=self.model_id,
            system=[
                {"text": system_prompt}
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": user_prompt}
                    ]
                }
            ],
            inferenceConfig={
                "maxTokens": 4096,
                "temperature": 0.2
            }
        )

        contents = response["output"]["message"]["content"]

        return "".join(
            item["text"]
            for item in contents
            if "text" in item
        )