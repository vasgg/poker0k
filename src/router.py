import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()
logger = logging.getLogger(__name__)


