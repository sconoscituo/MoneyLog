"""포트원(PortOne) 결제 연동 서비스"""
import httpx

PORTONE_API_URL = "https://api.iamport.kr"


async def get_access_token(api_key: str, api_secret: str) -> str:
    """포트원 액세스 토큰 발급"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PORTONE_API_URL}/users/getToken",
            json={"imp_key": api_key, "imp_secret": api_secret}
        )
        data = response.json()
        return data["response"]["access_token"]


async def verify_payment(imp_uid: str, expected_amount: int, api_key: str, api_secret: str) -> bool:
    """결제 금액 검증 - 위변조 방지"""
    token = await get_access_token(api_key, api_secret)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PORTONE_API_URL}/payments/{imp_uid}",
            headers={"Authorization": token}
        )
        data = response.json()
        paid_amount = data["response"]["amount"]
        return paid_amount == expected_amount


async def cancel_payment(imp_uid: str, reason: str, api_key: str, api_secret: str) -> dict:
    """결제 취소"""
    token = await get_access_token(api_key, api_secret)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PORTONE_API_URL}/payments/cancel",
            headers={"Authorization": token},
            json={"imp_uid": imp_uid, "reason": reason}
        )
        return response.json()
