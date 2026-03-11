# 聚宽API说明文档 
## 导入聚宽函数库

```python
import jqdata
```

## 函数说明
### **get_all_securities**

获取所有标的信息

```python
get_all_securities(types=[], date=None)
```

获取平台支持的所有股票、基金、指数、期货、期权信息

#### 参数说明

##### types
- **类型**: list
- **说明**: 用来过滤securities的类型，list元素可选：'stock', 'fund', 'index', 'futures', 'options', 'etf', 'lof', 'fja', 'fjb', 'open_fund', 'bond_fund', 'stock_fund', 'QDII_fund'(QDII基金), 'money_market_fund', 'mixture_fund'
- **注意**: types为空时返回所有股票，不包括基金、指数和期货

##### date
- **类型**: str 或 datetime.datetime/datetime.date 对象
- **说明**: 用于获取某日期还在上市的股票信息，默认值为 None，表示获取所有日期的股票信息
- **建议**: 使用该参数时添加上指定date

#### 返回值

- **pandas.DataFrame**，各 column 的含义如下：

| 字段 | 说明 |
|---|---|
| display_name | 中文名称，只返回最新的，判断是否st请使用get_extras |
| name | 缩写简称，同上 |
| start_date | 上市日期 |
| end_date | 退市日期（股票是最后一个交易日，不同于摘牌日期），如果没有退市则为2200-01-01 |
| type | 类型，stock(股票), index(指数), etf(场内ETF基金), fja（场内分级A）, fjb（场内分级B）, fjm（场内分级母基金）, mmf（场内交易的货币基金）, lof（上市型开放基金）, open_fund（开放式基金）, bond_fund（债券基金）, stock_fund（股票型基金）, money_market_fund（场外交易的货币基金）, mixture_fund（混合型基金）, fund_fund（联接基金）, options(期权) |

#### 示例

```python
def initialize(context):
    # 获得所有股票列表
    log.info(get_all_securities())
    log.info(get_all_securities(['stock']))
    
    # 获取所有股票代码转换成列表
    stocks = list(get_all_securities(['stock']).index)
    
    # 获取所有指数列表
    get_all_securities(['index'])
    
    # 获取所有基金
    df = get_all_securities(['fund'])
    
    # 获取所有期货列表
    get_all_securities(['futures'])
    
    # 获取所有期权列表
    get_all_securities(['options'])
    
    # 获取分级A基金列表
    df = get_all_securities(['fja'])
    
    # 获取lof基金列表
    df = get_all_securities(['lof'])
    
    # 获取分级A基金列表
    df = get_all_securities(['fja'])
    
    # 获取分级A基金列表
    df = get_all_securities(['fjb'])
    
    # 获取2015年10月10日还在上市的所有股票列表
    get_all_securities(date='2015-10-10')
    
    # 获取2015年10月10日还在上市的etf和lof基金列表
    get_all_securities(['etf', 'lof'], '2015-10-10')
```

### **get_price**

获取历史数据，可查询多个标的多个数据字段，返回数据格式为DataFrame

```python
get_price(security, start_date=None, end_date=None, frequency='1d', fields=None, skip_paused=False, fq='pre', count=None, panel=True, fill_paused=True)
```

#### 参数说明

##### security
- **类型**: 一支股票代码或一个股票代码的list
- **说明**: 要查询的标的代码

##### count
- **类型**: int
- **说明**: 与 start_date 二选一，不可同时使用。表示获取 end_date 之前几个 frequency 的数据

##### start_date
- **类型**: str 或 datetime.datetime/datetime.date 对象
- **说明**: 与 count 二选一，不可同时使用。表示起始时间
- **注意**:
  - 如果 count 和 start_date 参数都没有，则 start_date 生效，默认值是 '2015-01-01'
  - 当取分钟数据时，时间可以精确到分钟，比如：datetime.datetime(2015, 1, 1, 10, 0, 0)

##### end_date
- **类型**: str 或 datetime.datetime/datetime.date 对象
- **说明**: 结束时间，默认是 '2015-12-31'
- **注意**: 当取分钟数据时，如果 end_date 只有日期，则日内时间等同于 00:00:00，所以返回的数据不包含 end_date 这一天的

##### frequency
- **类型**: str
- **说明**: 单位时间长度，几分钟或者几天。现在支持 'Xd', 'Xm', 'daily'(等于'1d'), 'minute'(等于'1m')
- **注意**: X是一个正整数，分别表示X天和X分钟(不论是X天还是X分钟都会按每分钟的单位获取)，支持 '1d', '1m', '5m', '15m', '30m', '60m' 等
- **fields**: 默认是 ['open', 'close', 'high', 'low', 'volume', 'money'] 这几个标准字段

##### fields
- **类型**: list[str]
- **说明**: 获取数据的字段列表，默认为 ['open', 'close', 'high', 'low', 'volume', 'money']
- **可选值**: open(开盘价)、close(收盘价)、high(最高价)、low(最低价)、volume(成交量)、money(成交额)、factor(复权因子)、high_limit(涨停价)、low_limit(跌停价)、avg(均价)、pre_close(前收盘价)、paused(是否停牌)、open_interest(持仓量)

##### skip_paused
- **类型**: bool
- **说明**: 是否跳过不交易日期(包括停牌、上市前或者退市后)。默认False
- **注意**:
  - 当 skip_paused 是 True 时，获取多个标的需要指定panel为False

##### fq
- **类型**: str
- **说明**: 复权选项，取值的范围包括：
  - 'pre': 前复权
  - 'post': 后复权
  - 'None': 不复权

##### panel
- **类型**: bool
- **说明**: 在pandas 0.25版本后，panel被移除。获取多标的数据时建议设置panel=False，返回一个MultiIndex的DataFrame
- **默认**: True

##### fill_paused
- **类型**: bool
- **说明**: 对于停牌的价进行处理，默认为True。True表示用停牌时的数据进行补全。False表示NAN填充停牌的数据。

#### 合成数据的逻辑
当frequency为Xd和Xm分钟时，代表使用以X为长度的滑动窗口进行合并数据。举例：
- 9:33:00调用get_price获取1个单位的数据，frequency='5m'，表示使用上一交易日14:58、14:59、15:00、本交易日9:31、9:32这5根1分钟K线来合成数据；
- 9:37:00调用get_price获取1个单位的数据，frequency='5m'，表示使用本交易日9:32、9:33、9:34、9:35、9:36这5根1分钟K线来合成数据；

#### 返回
请注意，为了方便比较一只股票的多个属性，同时也满足对比多只股票的一个属性的需求，我们在security参数是一只股票和多只股票时返回的结构完全不一样(默认panel=False时)：

### 如果是一支股票
则返回pandas.DataFrame对象，行索引是datetime.datetime对象，列索引是行情字段名字，比如'open'/'close'。

**示例：**
```python
get_price('000300.XSHG')[1:2]
```

**返回：**
|  | open | close | high | low | volume | money |
|---|---|---|---|---|---|---|
| 2015-01-05 | 3566.09 | 3641.54 | 3669.04 | 3551.51 | 451198098.0 | 519849817448.0 |
| 2015-01-06 | 3608.43 | 3641.06 | 3683.23 | 3587.23 | 420962185.0 | 498529588258.0 |

### 如果是多支股票
则返回pandas.Panel对象，里面是很多pandas.DataFrame对象，索引是行情字段(open/close/...)，每个pandas.DataFrame的行索引是datetime.datetime对象，列索引是股票代码。

**示例：**
```python
get_price(['000300.XSHG', '000001.XSHG'])['open'][1:2]
```

**返回：**
|  | 000300.XSHG | 000001.XSHG |
|---|---|---|
| 2015-01-05 | 3566.09 | 13.21 |
| 2015-01-06 | 3608.43 | 13.09 |

#### 示例
```python
# 获取一支股票
# 获取000001.XSHG的2015年的按天数据
df = get_price('000001.XSHG')
# 获取000001.XSHG的2015年01月的分钟数据，只获取open+close字段
df = get_price('000001.XSHG', start_date='2015-01-01', end_date='2015-01-31 23:00:00', frequency='1m', fields=['open', 'close'])
# 获取000001.XSHG在2015年01月31日前2个交易日的数据
df = get_price('000001.XSHG', count = 2, end_date='2015-01-31', frequency='daily', fields=['open', 'close'])
# 获取000001.XSHG的2015年12月1号14:00-2015年12月2日12:00的分钟数据
df = get_price('000001.XSHG', start_date='2015-12-01 14:00:00', end_date='2015-12-02 12:00:00', frequency='1m')

# 获取多只股票
# 获取中证100的所有成分股的2015年的天数据，返回一个pandas.Panel
panel = get_price(get_index_stocks('000903.XSHG'))
# 获取开盘价的pandas.DataFrame，行索引是datetime.datetime对象，列索引是股票代号
df_open = panel['open']
# 获取成交量的pandas.DataFrame
df_volume = panel['volume']
# 获取平安银行的2015年每天的开盘价数据
df_open['000001.XSHG']
```

### **get_billboard_list**

获取龙虎榜数据

```python
get_billboard_list(stock_list, start_date, end_date, count)
```

获取指定日期区间内的龙虎榜数据

#### 参数

##### stock_list
- **类型**: 一个股票代码的list
- **说明**: 当值为 None 时，返回指定日期的所有股票

##### start_date
- **类型**: str 或 datetime.datetime/datetime.date 对象
- **说明**: 开始日期

##### end_date
- **类型**: str 或 datetime.datetime/datetime.date 对象
- **说明**: 结束日期

##### count
- **类型**: int
- **说明**: 交易日数量，可以与 end_date 同时使用，表示获取 end_date 前 count 个交易日的数据(含 end_date 当日)

#### 返回值

- **pandas.DataFrame**，各 column 的含义如下：

| 字段 | 说明 |
|---|---|
| code | 股票代码 |
| day | 日期 |
| direction | ALL 表示『汇总』，SELL 表示『卖』，BUY 表示『买』 |
| abnormal_code | 异常波动类型 |
| abnormal_name | 异常波动名称 |
| sales_depart_name | 营业部名称 |
| rank | 0 表示汇总，1~5 表示买一到买五，6~10 表示卖一到卖五 |
| buy_value | 买入金额 |
| buy_rate | 买入金额占比(买入金额/市场总成交额) |
| sell_value | 卖出金额 |
| sell_rate | 卖出金额占比(卖出金额/市场总成交额) |
| net_value | 净额(买入金额 - 卖出金额) |
| amount | 市场总成交额 |
| total_value | 买入卖出金额之和（买入金额+卖出金额） |

#### 示例

```python
# 在策略中获取前一日的龙虎榜数据
get_billboard_list(stock_list=None, end_date=context.previous_date, count=1)
```

### **get_index_stocks**

获取指数成份股

```python
get_index_stocks(index_symbol, date=None)
```

获取一个指数给定日期在平台可交易的成分股列表，请点击[指数列表](https://www.joinquant.com/help/api/help?name=index)查看指数信息

#### 参数

##### index_symbol
- **类型**: str
- **说明**: 指数代码

##### date
- **类型**: str 或 datetime.date/datetime.datetime 对象
- **说明**: 查询日期，一个字符串(格式类似'2015-10-15')或者datetime.date/datetime.datetime对象，可以是None，使用默认日期。这个默认日期在回测和研究模块上有点差别：
  - **回测模块**: 默认值会随着回测日期变化而变化，等于context.current_dt
  - **研究模块**: 默认是今天

#### 返回值

- **list**: 返回股票代码的list

#### 示例

```python
# 获取所有沪深300的股票
stocks = get_index_stocks('000300.XSHG')
log.info(stocks)
```

### **get_industry_stocks**

获取行业成份股

```python
get_industry_stocks(industry_code, date=None)
```

获取在给定日期一个行业的所有股票，行业分类列表见数据页面-[行业概念数据](https://www.joinquant.com/data/dict/industry)。

#### 参数

##### industry_code
- **类型**: str
- **说明**: 行业编码

##### date
- **类型**: str 或 datetime.date/datetime.datetime 对象
- **说明**: 查询日期，一个字符串(格式类似'2015-10-15')或者datetime.date/datetime.datetime对象，可以是None，使用默认日期。这个默认日期在回测和研究模块上有点差别：
  - **回测模块**: 默认值会随着回测日期变化而变化，等于context.current_dt
  - **研究模块**: 默认是今天

#### 返回值

- **list**: 返回股票代码的list

#### 示例

```python
# 获取计算机-互联网行业的成分股
stocks = get_industry_stocks('I64')
```

### **get_concept_stocks**

获取概念成份股

```python
get_concept_stocks(concept_code, date=None)
```

获取在给定日期一个概念板块的所有股票，概念板块分类列表见数据页面-[行业概念数据](https://www.joinquant.com/data/dict/concept)。

#### 参数

##### concept_code
- **类型**: str
- **说明**: 概念板块编码

##### date
- **类型**: str 或 datetime.date/datetime.datetime 对象
- **说明**: 查询日期，一个字符串(格式类似'2015-10-15')或者datetime.date/datetime.datetime对象，可以是None，使用默认日期。这个默认日期在回测和研究模块上有点差别：
  - **回测模块**: 默认值会随着回测日期变化而变化，等于context.current_dt
  - **研究模块**: 默认是今天

#### 返回值

- **list**: 返回股票代码的list

#### 示例

```python
# 获取风电概念板块的成分股
stocks = get_concept_stocks('SC0084', date='2019-04-16')
print(stocks)
```

#### 注意

- 申万在2014年2月21做了调整，2014年2月21日有几个行业被剔除了，同时又增加了新的行业，2014年2月21日之后的行业是28个，之前是23个，历史上总共有34个。

### **get_industries**

获取行业列表

```python
from jqdata import *
get_industries(name, date=None)
```

按照行业分类获取行业列表。

#### 参数

##### name
- **类型**: str
- **说明**: 行业代码，取值如下：
  - `"sw_l1"`: 申万一级行业
  - `"sw_l2"`: 申万二级行业
  - `"sw_l3"`: 申万三级行业
  - `"jq_l1"`: 聚宽一级行业
  - `"jq_l2"`: 聚宽二级行业
  - `"zjw"`: 证监会行业

##### date
- **类型**: str 或 datetime.date/datetime.datetime 对象
- **说明**: 获取数据的日期，默认为None，返回历史上所有行业；传入date，返回date当天存在的行业；研究和回测中返回结果相同；

#### 返回值

- **pandas.DataFrame**，各 column 的含义如下：

| 字段 | 说明 |
|---|---|
| index | 行业代码 |
| name | 行业名称 |
| start_date | 开始日期 |

#### 示例

```python
from jqdata import *
get_industries(name='zjw')
get_industries(name='zjw', date='2016-01-01')
```

### **get_concepts**

获取概念列表

```python
from jqdata import *
get_concepts()
```

获取所有的概念板块列表，行业分类列表见数据页面-[行业概念数据](https://www.joinquant.com/data/dict/concept)。

#### 返回值

- **pandas.DataFrame**，各 column 的含义如下：

| 字段 | 说明 |
|---|---|
| index | 概念代码 |
| name | 概念名称 |
| start_date | 开始日期 |

### **get_security_info**

获取单个标的信息

```python
get_security_info(code, date=None)
```

获取股票/基金/指数/期货的信息。

#### 参数

##### code
- **类型**: str
- **说明**: 证券代码

##### date
- **类型**: str 或 datetime.date 对象
- **说明**: 查询日期，默认为None，仅支持股票

#### 返回值

- **对象**，有如下属性：

| 属性 | 说明 |
|---|---|
| display_name | 中文名称 |
| name | 缩写简称 |
| start_date | 上市日期，[datetime.date]类型 |
| end_date | 退市日期（股票最后一个交易日，不同于摘牌日期），[datetime.date]类型，如果没有退市则为2200-01-01 |
| type | 股票、基金、金融期货、期货、债券基金、股票基金、QDII基金、货币基金、混合基金、场外基金；'stock' / 'fund' / 'index_futures' / 'futures' / 'etf' / 'bond_fund' / 'stock_fund' / 'QDII_fund' / 'money_market_fund' / 'mixture_fund' / 'open_fund' |
| parent | 分级基金的母基金代码 |

#### 示例

```python
# 获取000001.XSHG的上市时间
start_date = get_security_info('000001.XSHG').start_date
print(start_date)
```

### **get_industry**

查询股票所属行业

```python
get_industry(security, date=None)
```

查询股票所属行业。

#### 参数

##### security
- **类型**: str 或 list
- **说明**: 标的代码，类型为字符串，形如'000001.XSHG'；或为包含标的代码字符串的列表，形如['000001.XSHG', '000002.XSHE']

##### date
- **类型**: str 或 datetime.datetime/datetime.date 对象
- **说明**: 查询的日期，类型为字符串，形如'2018-06-01'或'2018-06-01 09:00:00'；或为datetime.datetime对象和datetime.date。注意传入对象的时分秒将被忽略。默认值为None，研究中默认值为当天，回测中默认值会随着回测日期变化而变化，等于context.current_dt。

#### 返回值

- **dict**，key是标的代码。

#### 示例

```python
>>> get_industry(security=['000001.XSHE', '000002.XSHE'], date='2018-06-01')

{'000001.XSHE': {'jq_l1': {'industry_code': 'HY007', 'industry_name': '金融指数'},
                 'jq_l2': {'industry_code': 'HY490', 'industry_name': '多元化银行指数'},
                 'sw_l1': {'industry_code': '801780', 'industry_name': '银行I'},
                 'sw_l2': {'industry_code': '801192', 'industry_name': '银行II'},
                 'sw_l3': {'industry_code': '851911', 'industry_name': '银行III'},
                 'zjw': {'industry_code': 'J66', 'industry_name': '货币金融服务'}
                },
 '000002.XSHE': {'jq_l1': {'industry_code': 'HY011', 'industry_name': '房地产指数'},
                 'jq_l2': {'industry_code': 'HY509', 'industry_name': '房地产开发指数'},
                 'sw_l1': {'industry_code': '801180', 'industry_name': '房地产I'},
                 'sw_l2': {'industry_code': '801181', 'industry_name': '房地产开发II'},
                 'sw_l3': {'industry_code': '851911', 'industry_name': '房地产开发III'},
                 'zjw': {'industry_code': 'K70', 'industry_name': '房地产业'}
                }
}
```

#### 注意

- python2中print打印一个unicode对象的时候，调用的是这个对象的`__str__`，而打印一个类似`{u'': u'中文'}`的时候，调用的是`__repr__`，因此可以这样使用：

```python
res = get_industry(security=['000001.XSHE', '000002.XSHE'], date='2018-06-01')
print(repr(res).decode('unicode-escape'))
```

### **get_concept**

获取股票所属概念板块

```python
get_concept(security, date=None)
```

获取股票所属概念板块，返回一个dict，key为标的代码，value详见示例。

#### 参数

##### security
- **类型**: str 或 list
- **说明**: 标的代码或包含标的代码的列表

##### date
- **类型**: str 或 datetime.date/datetime.datetime 对象
- **说明**: 要查询的日期，日期字符串/date对象/datetime对象，注意传入datetime对象时忽略日内时间；默认值为None，研究中默认值为当天，回测中默认值会随着回测日期变化而变化，等于context.current_dt。

#### 返回值

- **dict**，key是标的代码，value包含概念板块信息。

返回数据结构示例：

```python
{
    'code': {
        'jq_concept': [
            {'concept_code': 'XX1', 'concept_name': 'YY1'},
            {'concept_code': 'XX2', 'concept_name': 'YY2'},
            {'concept_code': 'XX3', 'concept_name': 'YY3'}
        ]
    }
}
```

- `code`是传入的股票代码，多个code返回嵌套的多个字典
- `jq_concept`代表聚宽概念
- `XX`是code所在的概念代码
- `YY`是code所在的概念名称

#### 示例

```python
dict1 = get_concept('000001.XSHE', date='2019-07-15')
print(dict1)
```

### **get_all_trade_days**

获取所有交易日

```python
from jqdata import *
get_all_trade_days()
```

获取所有交易日，不需要传入参数，返回一个包含所有交易日的 numpy.ndarray，每个元素为一个datetime.date类型。

**注：需导入 jqdata 模块，即在策略或研究起始位置加入**

```python
import jqdata
```

### **get_trade_days**

获取指定范围交易日

```python
from jqdata import *
get_trade_days(start_date=None, end_date=None, count=None)
```

获取指定日期范围内的所有交易日，返回一个包含datetime.date object的列表，包含指定的 start_date 和 end_date，默认返回至 datetime.date.today() 的所有交易日。

**注意**：get_trade_days最多只能获取到截至现实时间的当前年份的最后一天的交易日数据。

**注：需导入 jqdata 模块，即在策略或研究起始位置加入**

```python
import jqdata
```

#### 参数

##### start_date
- **类型**: str 或 datetime.date/datetime.datetime 对象
- **说明**: 开始日期，与 count 二选一，不可同时使用

##### end_date
- **类型**: str 或 datetime.date/datetime.datetime 对象
- **说明**: 结束日期，默认为 datetime.date.today()

##### count
- **类型**: int
- **说明**: 数量，与 start_date 二选一，不可同时使用，必须大于 0，表示取 end_date 往前的 count 个交易日，包含 end_date 当天。

### **get_money_flow**

获取资金流信息

```python
from jqdata import *
get_money_flow(security_list, start_date=None, end_date=None, fields=None, count=None)
```

获取一只或者多只股票在一个时间段内的资金流向数据，仅包含股票数据，不可用于获取期货数据。

提供2010年至今的数据，数据频率为天。

净额：为正资金流入，为负为资金流出。

#### 参数

##### security_list
- **类型**: str 或 list
- **说明**: 一只股票代码或者一个股票代码的 list

##### start_date
- **类型**: str 或 datetime.datetime/datetime.date 对象
- **说明**: 开始日期，与 count 二选一，不可同时使用，默认为平台提供的数据的最早日期

##### end_date
- **类型**: str 或 datetime.date/datetime.datetime 对象
- **说明**: 结束日期，默认为 datetime.date.today()

##### count
- **类型**: int
- **说明**: 数量，与 start_date 二选一，不可同时使用，必须大于 0，表示返回 end_date 之前 count 个交易日的数据，包含 end_date

##### fields
- **类型**: str 或 list
- **说明**: 字段名或者 list，可选，默认为 None，表示取全部字段

#### 字段说明

| 字段名 | 含义 | 备注 |
|---|---|---|
| date | 日期 | --- |
| sec_code | 股票代码 | --- |
| change_pct | 涨跌幅(%) | --- |
| net_amount_main | 主力净额(万) | 主力净额 = 超大单净额 + 大单净额 |
| net_pct_main | 主力净占比(%) | 主力净占比 = 主力净额 / 成交额 |
| net_amount_xl | 超大单净额(万) | 超大单：大于等于50万股或者100万元的成交单 |
| net_pct_xl | 超大单净占比(%) | 超大单净占比 = 超大单净额 / 成交额 |
| net_amount_l | 大单净额(万) | 大单：大于等于10万股或者20万元且小于50万股或者100万元的成交单 |
| net_pct_l | 大单净占比(%) | 大单净占比 = 大单净额 / 成交额 |
| net_amount_m | 中单净额(万) | 中单：大于等于2万股或者4万元且小于10万股或者20万元的成交单 |
| net_pct_m | 中单净占比(%) | 中单净占比 = 中单净额 / 成交额 |
| net_amount_s | 小单净额(万) | 小单：小于2万股或者4万元的成交单 |
| net_pct_s | 小单净占比(%) | 小单净占比 = 小单净额 / 成交额 |

#### 返回值

- **pandas.DataFrame** 对象，默认的列索引为取得的全部字段，如果给定了 fields 参数，则列索引与给定的 fields 对应。

#### 示例

```python
from jqdata import *

# 获取一只股票在一个时间段内的资金流量数据
get_money_flow('000001.XSHE', '2016-02-01', '2016-02-04')
get_money_flow('000001.XSHE', '2015-10-01', '2015-12-30', fields="change_pct")
get_money_flow(['000001.XSHE'], '2010-01-01', '2010-01-30', ["date", "sec_code", "change_pct", "net_amount_main", "net_pct_l", "net_amount_m"])

# --------------------------------------------------

# 获取多只股票在一个时间段内的资金流向数据
get_money_flow(['000001.XSHE', '000040.XSHE', '000099.XSHE'], '2010-01-01', '2010-01-30')
# 获取多只股票在某一天的资金流向数据
get_money_flow(['000001.XSHE', '000040.XSHE', '000099.XSHE'], '2016-04-01', '2016-04-01')

# --------------------------------------------------

# 获取股票 000001.XSHE 在日期 2016-06-30 往前 20 个交易日的资金流量数据
get_money_flow('000001.XSHE', end_date="2016-06-30", count=20)
# 获取股票 000001.XSHE 往前 20 个交易日的资金流量数据
get_money_flow('000001.XSHE', count=20)
```

#### 注意

- 需要导入：`from jqdata import *`
- 在回测中，为避免未来函数，无法获取回测当前逻辑时间的那一条数据（所以有时会出现实际获取数据比count少一条的现象）

### **normalize_code**

股票代码格式转换

```python
normalize_code(code)
```

将其他形式的股票代码转换为聚宽可用的股票代码形式。

仅适用于A股市场股票代码、期货以及场内基金代码，输入字符串格式或int格式的其他形式标的代码，也支持list或tuple来转换多个标的代码。

#### 参数

##### code
- **类型**: str, int, list 或 tuple
- **说明**: 要转换的股票代码，可以是单个字符串（如'000001'）、整数，或多个代码的list/tuple

#### 返回值

| 返回值类型 | 说明 |
|---|---|
| str | 输入单个代码时，返回转换后的单个字符串，如'000001.XSHE' |
| list | 输入list/tuple时，返回转换后的代码列表，如['000001.XSHE', '000002.XSHE'] |

#### 示例

```python
# 输入
codes = ('000001', 'SZ000001', '000001SZ', '000001.sz', '000001.XSHE')
print(normalize_code(codes))

# 输出
['000001.XSHE', '000001.XSHE', '000001.XSHE', '000001.XSHE', '000001.XSHE']
```

