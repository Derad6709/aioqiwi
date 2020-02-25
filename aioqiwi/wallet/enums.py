from ..utils.autoenum import NamedEnum, auto


class PaymentTypes(NamedEnum):
    IN = auto()
    OUT = auto()
    QIWI_CARD = auto()
    ALL = auto()


class PaymentSources(NamedEnum):
    """Источники платежа, для отбора. Каждый источник задается как отдельный параметр и нумеруется элементом массива, начиная с нуля (sources[0], sources[1] и т.д.). Допустимые значения:
    QW_RUB - рублевый счет кошелька,
    QW_USD - счет кошелька в долларах,
    QW_EUR - счет кошелька в евро,
    CARD - привязанные и непривязанные к кошельку банковские карты,
    MK - счет мобильного оператора. Если не указаны, учитываются все источники"""

    QW_RUB = auto()
    QW_USD = auto()
    QW_EUR = auto()
    CARD = auto()
    MK = auto()


class Provider(NamedEnum):
    """
    99 - Перевод на QIWI Wallet

    1963 - Перевод на карту Visa (карты российских банков)
    21013 - Перевод на карту MasterCard (карты российских банков)
    Для карт, выпущенных банками стран Азербайджан, Армения, Белоруссия, Грузия, Казахстан, Киргизия, Молдавия,
    Таджикистан, Туркменистан, Украина, Узбекистан:
        1960 – Перевод на карту Visa
        21012 – Перевод на карту MasterCard

    31652 - Перевод на карту национальной платежной системы МИР
    466 - Тинькофф Банк
    464 - Альфа-Банк
    821 - Промсвязьбанк
    815 - Русский Стандарт
    Идентификаторы операторов мобильной связи
    Идентификаторы других провайдеров
    1717 - платеж по банковским реквизитам"""

    QIWI_WALLET = 99

    VISA_RU = 1963
    VISA_FOREIGN = 1960

    MASTERCARD_RU = 21013
    MASTERCARD_FOREIGN = 21012

    MIR_CARD = 31652

    TINKOFF_BANK = 466
    ALPHA_BANK = 464
    PROSVYAZ_BANK = 821
    RUSSKIY_STANDART = 815

    CUSTOM = 1717


class ChequeTypes(NamedEnum):
    """
    Check [Cheque]'s output type
    """

    JPEG = auto()
    PDF = auto()
