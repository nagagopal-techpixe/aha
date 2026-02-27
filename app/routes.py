from fastapi import APIRouter, HTTPException
from typing import List
from bson import ObjectId
from bson.errors import InvalidId
from app.models import ReviewBase, ReviewResponse
from app.database import review_collection
from datetime import datetime,timedelta
import httpx,json
import re

router = APIRouter()

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/cfzcjbihnsk3qbkhwa5a67rtz3ppvcef"


def review_helper(review) -> dict:
    return {
        "id": str(review["_id"]),
        "title": review.get("title"),
        "content": review.get("content"),
        "image_url": review.get("image_url"),
        "meta_description": review.get("meta_description"),
        "focus_keyword": review.get("focus_keyword"),
        "seo_tags": review.get("seo_tags", []),
        "created_at": review.get("created_at")
    }

@router.post("/generate-review/", response_model=ReviewResponse)
async def generate_review(payload: dict):

    try:
        # -----------------------------
        #  Check Daily Limit (Before Webhook)
        # -----------------------------

        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        tomorrow_start = today_start + timedelta(days=1)

        today_count = await review_collection.count_documents({
            "created_at": {
                "$gte": today_start,
                "$lt": tomorrow_start
            }
        })

        if today_count >= 2:
            raise HTTPException(
                status_code=429,
                detail="Daily limit reached. Only 2 reviews allowed per day."
            )

        # -----------------------------
        #  Call Webhook
        # -----------------------------

        async with httpx.AsyncClient() as client:
            webhook_response = await client.post(
                MAKE_WEBHOOK_URL,
                json=payload,
                timeout=600
            )

        raw_text = webhook_response.text.strip()

        # -----------------------------
        # 3️⃣ Clean Webhook Response
        # -----------------------------

        raw_text = raw_text.replace("```json", "").replace("```", "")
        raw_text = re.sub(r'^Content\s*:\s*', '', raw_text).strip()

        def escape_newlines_in_strings(text):
            inside_string = False
            result = []

            for char in text:
                if char == '"' and (not result or result[-1] != '\\'):
                    inside_string = not inside_string
                    result.append(char)
                elif char == '\n' and inside_string:
                    result.append('\\n')
                else:
                    result.append(char)

            return ''.join(result)

        clean_text = escape_newlines_in_strings(raw_text)

        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid JSON from webhook: {str(e)}"
            )

        # -----------------------------
        #  Save to MongoDB
        # -----------------------------

        review_data = {
            "title": data.get("title"),
            "content": data.get("content"),
            "image_url": data.get("image_url"),
            "meta_description": data.get("meta_description"),
            "focus_keyword": data.get("focus_keyword"),
            "seo_tags": data.get("seo_tags", []),
            "created_at": datetime.utcnow()
        }

        result = await review_collection.insert_one(review_data)
        new_review = await review_collection.find_one({"_id": result.inserted_id})

        return review_helper(new_review)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))   
#  Get all reviews
@router.get("/reviews/", response_model=List[ReviewResponse])
async def get_reviews():
    reviews = []
    async for review in review_collection.find():
        reviews.append(review_helper(review))
    return reviews


#  Get review by ID
@router.get("/reviews/{id}", response_model=ReviewResponse)
async def get_review(id: str):
    try:
        review = await review_collection.find_one({"_id": ObjectId(id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid review ID")

    if review:
        return review_helper(review)

    raise HTTPException(status_code=404, detail="Review not found")