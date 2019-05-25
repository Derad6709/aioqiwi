import asyncio
import logging
import uuid
import base64

from aiohttp import web

from .models import sent_invoice, refund
from .handler import Handler
from . import server

from ..urls import Urls
from ..mixin import QiwiMixin, serialize
from ..utils.currency_utils import Currency
from ..utils.time_utils import TimeRange
from ..utils.phone import parse_phone


logger = logging.getLogger("aioqiwi")
_get_loop = asyncio.get_event_loop  # noqa


class QiwiKassa(QiwiMixin):
    def __init__(self, api_hash: str, loop: asyncio.AbstractEventLoop = None):
        """
        Beta of kassa.qiwi.com currently developing
        :param api_hash: Qiwi unique token given for an account
        """
        session = self._new_http_session(api_hash)
        self.__session = session

        self.__api_hash = api_hash

        self.__get = session.get
        self.__post = session.post
        self.__put = session.put
        self.__delete = session.delete
        self.__patch = session.patch

        self.__loop = loop or _get_loop()
        self.__handler = Handler(self.__loop)

    @staticmethod
    def generate_bill_id():
        """
        Generates unique bill_id
        However you can implement your generator :idk:
        """
        return (
            base64.urlsafe_b64encode(uuid.uuid3(uuid.uuid4(), "").bytes)
            .decode()
            .rstrip("=")
            .upper()
        )

    async def new_bill(
        self,
        amount: float,
        peer: int or str = None,
        peer_email: str = None,
        lifetime: TimeRange = TimeRange(10),
        currency: str or int or Currency = Currency["rub"],
        comment: str = "via aioqiwi",
        bill_id: str = None,
    ) -> sent_invoice.Invoice:
        """
        Create new bill
        :param amount: invoice amount rounded down to two decimals
        :param peer: phone number to which invoice issued
        :param peer_email: client's e-mail
        :param lifetime: invoice due date, pass TimeRange class which is cool and convenient
        :param currency: pass Currency object or integer code like <845> of currency or str code like <'USD'>
        :param comment: invoice commentary
        :param bill_id: unique invoice identifier in merchant's system
        :return: SentInvoice if success
        """
        ccode = (
            currency.code
            if isinstance(currency, Currency.currency)
            else Currency[currency].code
        )
        url = Urls.P2PBillPayments.bill.format(bill_id or self.generate_bill_id())

        data = serialize(
            self._param_filter(
                {
                    "amount": {"currency": ccode, "value": amount},
                    "comment": comment,
                    "expirationDateTime": lifetime.to_date.today,
                    "customer": {"phone": parse_phone(peer), "account": peer_email}
                    if peer and peer_email
                    else {},
                    "customFields": {},
                }
            )
        )

        async with self.__put(data=data, url=url) as response:
            return await self._make_return(response, sent_invoice.Invoice)

    async def bill_info(self, bill_id: str) -> sent_invoice.Invoice:
        """
        Get info about bill
        :param bill_id: bill's id in your system
        :return: kassa.models.Invoice instance
        """
        url = Urls.P2PBillPayments.bill.format(bill_id)

        async with self.__get(url) as response:
            return await self._make_return(response, sent_invoice.Invoice)

    async def reject_bill(self, bill_id: str):
        """
        Reject bill
        :param bill_id: bill's id in your system
        :return: kassa.models.Invoice
        """
        url = Urls.P2PBillPayments.reject.format(bill_id)

        async with self.__post(url) as response:
            return await self._make_return(response, sent_invoice.Invoice)

    async def refund(
        self,
        bill_id: str,
        refund_id: str,
        amount: float = None,
        currency: str or int = None,
    ) -> refund.Refund:
        """
        Refund user's money, pass amount and currency to refund, else will get info about refund
        :param bill_id: bill's id in your system
        :param refund_id: refund id
        :param amount: amount to refund
        :param currency: currency
        :return: Refund class instance
        """
        url = Urls.P2PBillPayments.refund.format(bill_id, refund_id)

        if not amount and not currency:
            async with self.__get(url) as response:
                return await self._make_return(response, refund.Refund)

        data = serialize(
            self._param_filter(
                {"amount": {"currency": self.get_currency(currency), "value": amount}}
            )
        )

        async with self.__put(url, data=data) as response:
            return await self._make_return(response, refund.Refund)

    def on_update(self) -> Handler.update:
        """
        Return function, use it as a decorator
        :return:
        """
        return self.__handler.update

    def configure_listener(self, app, path=None):
        """
        Pass aiohttp.web.Application and aioqiwi.kassa.server will bind itself to your app
        :param app:
        :return:
        """
        server.setup(self.__api_hash, self.__handler, app, path=path)

    def idle(self, host="localhost", port=6969, path=None, app=None):
        """
        [WARNING] This is blocking io method
        :param host: server host
        :param port: server port that open for tcp/ip trans.
        :param path: path for qiwi that will send requests
        :param app: pass web.Application if you want, common-use - aiogram powered webhook-bots
        :return:
        """
        server.setup(self.__handler, app or web.Application(), path)
        web.run_app(app, host=host, port=port)

    # session-related
    async def close(self):
        await self.__session.close()

    # `async with` block
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
