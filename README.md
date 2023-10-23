# super-trader
목표: 모든 거래소에 대해 동일한 로직으로 거래할 수 있는 기초 트레이딩 시스템 구축

```config.json``` 파일 예시
```
{
    "creon": {
        "id": "******",
        "pwd": "******",
        "pwdcert": "******"
    },
    "binance": {
        "api_key": "******",
        "secret": "******"
    },
    "db": {
        "host": "localhost",
        "user": "root",
        "password": "******",
        "db": "stock_info",
        "charset": "utf8"
    },
    "slack": {
        "token": "******",
        "channel": "#trader"
    },
    "holiday": {
        "2023": [
            20230123,
            20230124,
            ...,
            20231225,
            20231229
        ]
    }
}
```
