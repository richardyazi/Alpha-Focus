# -*- coding: utf-8 -*-
"""
聚宽选股程序 - 关键K线标记模块
功能：标记股票K线序列中的关键K线（小阴小阳、十字星、B1）
"""

import pandas as pd
import numpy as np
import os
import datetime
from datetime import datetime as dt, timedelta, date
from jqdata import *



def get_script_dir():
    """
    获取脚本所在目录
    兼容脚本环境和Jupyter Notebook环境
    """
    try:
        # 脚本环境：获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # Jupyter Notebook环境：从模块对象获取路径
        try:
            import inspect
            current_dir = os.path.dirname(os.path.abspath(inspect.getfile(get_script_dir)))
        except (NameError, TypeError):
            # 如果都无法获取，使用当前工作目录
            current_dir = os.getcwd()
    return current_dir


def get_stock_cache_dir():
    """
    获取股票缓存池目录路径
    """
    script_dir = get_script_dir()
    cache_dir = os.path.join(script_dir, 'stock_cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir


def get_last_complete_trading_day():
    """
    获取最后一个完整交易日
    数据已完整收录且交易日已结束的日期（不含当日）
    """
    from jqdata import get_trade_days

    # 获取截至今天的所有交易日

    trade_days = get_trade_days(end_date=date.today(), count=5)

    if len(trade_days) == 0  :
        return None

    # 如果今天是交易日，返回倒数第二个交易日（因为当日数据可能不完整）
    # 如果今天不是交易日，返回最后一个交易日
    today = date.today()
    if trade_days[-1] == today:
        # 今天是交易日，返回倒数第二个交易日
        last_complete = trade_days[-2]
    else:
        # 今天不是交易日，返回最后一个交易日
        last_complete = trade_days[-1]

    return last_complete.strftime('%Y-%m-%d')



def get_stock_list_date(stock_code):
    """
    获取股票上市日期
    """
    try:
        stock_info = get_security_info(stock_code)
        if stock_info:
            return stock_info.start_date
    except:
        pass
    return None


def get_cache_file_path(stock_code):
    """
    根据股票代码获取缓存文件路径
    格式: stock_cache/上市年月/股票代码.csv
    """
    list_date = get_stock_list_date(stock_code)
    if list_date:
        year_month = list_date.strftime('%Y-%m')
    else:
        year_month = 'unknown'
    cache_dir = get_stock_cache_dir()
    cache_subdir = os.path.join(cache_dir, year_month)
    if not os.path.exists(cache_subdir):
        os.makedirs(cache_subdir)
    return os.path.join(cache_subdir, f'{stock_code}.csv')


def load_cached_stock_data(stock_code):
    """
    从缓存池加载股票数据
    """
    cache_file = get_cache_file_path(stock_code)
    if not os.path.exists(cache_file):
        return None

    try:
        df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        return df
    except Exception as e:
        print(f"警告: 读取缓存文件 {cache_file} 失败: {str(e)}")
        return None


def save_cached_stock_data(stock_code, df):
    """
    保存股票数据到缓存池
    """
    cache_file = get_cache_file_path(stock_code)
    try:
        df.to_csv(cache_file)
        return True
    except Exception as e:
        print(f"警告: 保存缓存文件 {cache_file} 失败: {str(e)}")
        return False


def check_data_completeness(df, stock_code):
    """
    检查缓存数据是否完整
    检查日期范围是否覆盖从上市日到最后一个完整交易日
    """
    if df is None or df.empty:
        return False

    list_date = get_stock_list_date(stock_code)
    if not list_date:
        return False

    last_complete_day = get_last_complete_trading_day()

    # 检查缓存数据的起始日期和结束日期
    cached_start = df.index.min()
    cached_end = df.index.max()

    list_date_dt = pd.Timestamp(list_date)
    last_complete_day_dt = pd.Timestamp(last_complete_day)

    # 检查是否覆盖上市日到最后一个完整交易日
    return cached_start <= list_date_dt and cached_end >= last_complete_day_dt


def update_cached_stock_data(stock_code):
    """
    更新股票缓存数据
    查询上市日到最后一个完整交易日的历史数据并缓存
    """
    list_date = get_stock_list_date(stock_code)
    if not list_date:
        print(f"警告: 无法获取股票 {stock_code} 的上市日期")
        return None

    last_complete_day = get_last_complete_trading_day()

    try:
        # 查询股票日线数据（前复权）
        df = get_price(
            security=stock_code,
            start_date=list_date.strftime('%Y-%m-%d'),
            end_date=last_complete_day,
            frequency='1d',
            fields=['open', 'close', 'high', 'low', 'volume', 'money'],
            fq='pre'
        )

        if df.empty:
            print(f"警告: 股票 {stock_code} 未获取到数据")
            return None

        # 保存到缓存池
        save_cached_stock_data(stock_code, df)
        return df
    except Exception as e:
        print(f"警告: 更新股票 {stock_code} 缓存数据失败: {str(e)}")
        return None


def get_stock_data_with_cache(stock_code, start_date, end_date):
    """
    使用缓存池获取股票数据
    如果缓存中无数据或不完整，则更新缓存
    如果起始日期和结束日期之间包含未结束的交易日或未来时间，则调用API获取额外数据

    参数：
        stock_code: str, 股票代码
        start_date: str, 起始日期 (格式: 'YYYY-MM-DD')
        end_date: str, 结束日期 (格式: 'YYYY-MM-DD')

    返回：
        DataFrame: 股票日线数据，index为交易时间，columns为['open', 'close', 'high', 'low', 'volume', 'money']
    """
    # 尝试从缓存加载
    cached_df = load_cached_stock_data(stock_code)

    # 如果缓存不存在或数据不完整，则更新缓存
    if cached_df is None or not check_data_completeness(cached_df, stock_code):
        cached_df = update_cached_stock_data(stock_code)
        if cached_df is None or cached_df.empty:
            return pd.DataFrame()

    # 从缓存数据中获取指定时间范围的数据
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    # 获取缓存数据中覆盖的日期范围
    cached_start = cached_df.index.min()
    cached_end = cached_df.index.max()

    result_df = None

    # 如果请求的结束日期超过缓存数据的结束日期（可能包含未结束的交易日或未来日期）
    if end_dt > cached_end:
        # 获取缓存数据中在请求起始日期之前的部分
        if start_dt <= cached_end:
            cached_part = cached_df.loc[start_dt:cached_end]
            result_df = cached_part
        else:
            result_df = pd.DataFrame()

        # 调用API获取额外的数据
        try:
            extra_start = max(cached_end + timedelta(days=1), start_dt)
            extra_df = get_price(
                security=stock_code,
                start_date=extra_start.strftime('%Y-%m-%d'),
                end_date=end_date,
                frequency='1d',
                fields=['open', 'close', 'high', 'low', 'volume', 'money'],
                fq='pre'
            )

            if not extra_df.empty:
                # 合并缓存数据和实时数据，确保时间顺序正确且无重复
                if result_df is not None and not result_df.empty:
                    # 使用pd.concat合并，并通过去重避免重复数据
                    combined = pd.concat([result_df, extra_df])
                    result_df = combined[~combined.index.duplicated(keep='last')].sort_index()
                else:
                    result_df = extra_df
        except Exception as e:
            print(f"警告: 获取股票 {stock_code} 额外数据失败: {str(e)}")
    else:
        # 请求的日期范围完全在缓存内
        result_df = cached_df.loc[start_dt:end_date]

    return result_df if result_df is not None else pd.DataFrame()





def calculate_kline_indicators(df):
    """
    计算K线技术指标

    参数：
        df: DataFrame, 包含开高低收成交量等数据
            columns: ['open', 'close', 'high', 'low', 'volume']

    返回：
        dict: 包含各种技术指标的字典
    """
    # 白线: EMA(EMA(C,10),10)
    ema1 = df['close'].ewm(span=10, adjust=False).mean()
    white_line = ema1.ewm(span=10, adjust=False).mean()

    # 黄线：(MA(CLOSE,14)+MA(CLOSE,28)+MA(CLOSE,57)+MA(CLOSE,114))/4
    ma14 = df['close'].rolling(window=14).mean()
    ma28 = df['close'].rolling(window=28).mean()
    ma57 = df['close'].rolling(window=57).mean()
    ma114 = df['close'].rolling(window=114).mean()
    yellow_line = (ma14 + ma28 + ma57 + ma114) / 4

    # 百日移动平均成交量
    ma_vol_100 = df['volume'].rolling(window=100).mean()

    # KDJ指标（防止除零错误）
    low_9 = df['low'].rolling(window=9).min()
    high_9 = df['high'].rolling(window=9).max()
    high_low_diff = high_9 - low_9
    # 使用np.where避免除零，当最高价等于最低价时，RSV设为50
    rsv = np.where(high_low_diff != 0,
                  (df['close'] - low_9) / high_low_diff * 100,
                  50)
    rsv = pd.Series(rsv, index=df.index)
    k = rsv.ewm(com=2, adjust=False).mean()
    d = k.ewm(com=2, adjust=False).mean()
    j = 3 * k - 2 * d

    # 前一日收盘价
    pre_close = df['close'].shift(1)

    return {
        'white_line': white_line,
        'yellow_line': yellow_line,
        'ma_vol_100': ma_vol_100,
        'j': j,
        'pre_close': pre_close
    }


def check_small_yang_yin(df, indicators):
    """
    检查小阴小阳K线

    参数：
        df: DataFrame, 包含K线数据
        indicators: dict, 包含技术指标

    返回：
        Series: Boolean Series，标记是否为小阴小阳
    """
    # 当日成交量小于百日移动平均成交量
    condition1 = df['volume'] < indicators['ma_vol_100']

    # 当日股价涨幅在-2%~1.8%之间
    # (今日收盘价 - 昨日收盘价) / 昨日收盘价 >= -0.02 and <= 0.018
    # 使用np.where和pd.isna避免除零和NaN警告
    with np.errstate(invalid='ignore'):
        price_change = np.where((indicators['pre_close'] != 0) & (~pd.isna(indicators['pre_close'])),
                                (df['close'] - indicators['pre_close']) / indicators['pre_close'],
                                0)
    condition2 = (price_change >= -0.02) & (price_change <= 0.018)

    # 当日股价振幅小于7%
    # (最高价 - 最低价) / 昨日收盘价 <= 0.07
    with np.errstate(invalid='ignore'):
        amplitude = np.where((indicators['pre_close'] != 0) & (~pd.isna(indicators['pre_close'])),
                             (df['high'] - df['low']) / indicators['pre_close'],
                             0)
    condition3 = amplitude <= 0.07

    return condition1 & condition2 & condition3


def check_doji(df, small_yang_yin):
    """
    检查十字星K线

    参数：
        df: DataFrame, 包含K线数据
        small_yang_yin: Series, 小阴小阳标记

    返回：
        Series: Boolean Series，标记是否为十字星
    """
    # 开盘价与收盘价之差的绝对值相对于开盘价的比例小于1%
    # |开盘价 - 收盘价| / 开盘价 < 0.01
    # 使用np.where和pd.isna避免除零和NaN警告
    with np.errstate(invalid='ignore'):
        open_close_diff = np.where((df['open'] != 0) & (~pd.isna(df['open'])),
                                   abs(df['open'] - df['close']) / df['open'],
                                   0)
    condition = open_close_diff < 0.01

    return small_yang_yin & condition


def check_b1(df, indicators, small_yang_yin, debug=False):
    """
    检查B1 K线

    参数：
        df: DataFrame, 包含K线数据
        indicators: dict, 包含技术指标
        small_yang_yin: Series, 小阴小阳标记
        debug: bool, 是否打印调试信息，默认为False

    返回：
        Series: Boolean Series，标记是否为B1
    """
    # 满足小阴小阳条件
    condition1 = small_yang_yin

    # 白线在黄线之上
    condition2 = indicators['white_line'] > indicators['yellow_line']

    # 股价在黄线之上
    condition3 = df['close'] > indicators['yellow_line']

    # 当日KDJ的J值 < 14
    condition4 = indicators['j'] < 14

    b1_result = condition1 & condition2 & condition3 & condition4

    # 调试信息：打印所有B1标记的K线详细信息
    if debug:
        b1_dates = df.index[b1_result]
        if len(b1_dates) > 0:
            print("\n" + "="*80)
            print("B1标记K线详细信息：")
            print("="*80)
            for date in b1_dates:
                print(f"\n日期: {date.strftime('%Y-%m-%d')}")
                print("-"*80)
                print(f"K线数据:")
                print(f"  开盘价: {df.loc[date, 'open']:.2f}")
                print(f"  收盘价: {df.loc[date, 'close']:.2f}")
                print(f"  最高价: {df.loc[date, 'high']:.2f}")
                print(f"  最低价: {df.loc[date, 'low']:.2f}")
                print(f"  成交量: {df.loc[date, 'volume']:.0f}")
                print(f"\n技术指标:")
                print(f"  白线(EMA): {indicators['white_line'].loc[date]:.2f}")
                print(f"  黄线(MA):  {indicators['yellow_line'].loc[date]:.2f}")
                print(f"  白线-黄线:  {indicators['white_line'].loc[date] - indicators['yellow_line'].loc[date]:.2f}")
                print(f"  百日均量:  {indicators['ma_vol_100'].loc[date]:.0f}")
                print(f"  KDJ-J值:   {indicators['j'].loc[date]:.2f}")
                print(f"\n判断条件:")
                print(f"  小阴小阳:   {condition1.loc[date]}")
                print(f"  白线>黄线:  {condition2.loc[date]}")
                print(f"  股价>黄线:  {condition3.loc[date]}")
                print(f"  J值<14:     {condition4.loc[date]}")
                print("-"*80)
            print("="*80)
        else:
            print("\n未发现B1标记K线")

    return b1_result


def resample_kline(df, frequency):
    """
    按周期聚合K线数据

    参数：
        df: DataFrame, 日线数据
        frequency: str, K线周期 ('1d', '1w', '1m', '3m', '6m', '1y')

    返回：
        DataFrame: 聚合后的K线数据
    """
    if frequency == '1d':
        return df

    # 映射聚宽频率到pandas resample规则
    freq_map = {
        '1w': 'W-FRI',  # 以周五为周末
        '1m': 'M',      # 月末
        '3m': '3M',     # 季末
        '6m': '6M',     # 半年末
        '1y': 'A'       # 年末
    }

    rule = freq_map.get(frequency, 'D')

    # 聚合数据
    resampled = pd.DataFrame()
    resampled['open'] = df['open'].resample(rule).first()
    resampled['high'] = df['high'].resample(rule).max()
    resampled['low'] = df['low'].resample(rule).min()
    resampled['close'] = df['close'].resample(rule).last()
    resampled['volume'] = df['volume'].resample(rule).sum()
    resampled['money'] = df['money'].resample(rule).sum()

    return resampled.dropna()


def calculate_required_start_date(start_date, frequency):
    """
    根据K线周期和指标计算所需的历史数据长度，动态计算起始日期
    基于用户输入的起始日期向前扩展，确保有足够的历史数据计算技术指标

    参数：
        start_date: str, 用户输入的起始日期 (格式: 'YYYY-MM-DD')
        frequency: str, K线周期 ('1d', '1w', '1m', '3m', '6m', '1y')

    返回：
        str: 实际获取数据的起始日期 (格式: 'YYYY-MM-DD')
    """
    # 各技术指标所需的最大周期（以交易日计）
    # MA114需要114个交易日，是最大的指标需求
    max_required_days = 114

    # 根据K线周期调整所需天数
    # 周线需要约5倍、月线约20倍等的历史数据来保证有足够的周期数
    frequency_multiplier = {
        '1d': 1,   # 日线：直接需要114个交易日
        '1w': 5,   # 周线：114个交易日 ≈ 23周，需要约115个交易日
        '1m': 20,  # 月线：114个交易日 ≈ 6个月，需要约120个交易日
        '3m': 60,  # 季线：需要更多历史数据保证至少有足够的季度数
        '6m': 120, # 半年线
        '1y': 240  # 年线
    }

    multiplier = frequency_multiplier.get(frequency, 1)
    required_days = max_required_days * multiplier

    # 使用get_trade_days精确计算起始日期
    # 获取start_date往前required_days个交易日的日期
    trade_days = get_trade_days(end_date=start_date, count=required_days + 1)
    # trade_days[-1]是start_date，trade_days[0]是第required_days+1个交易日
    # 我们取trade_days[0]作为起始日期
    if len(trade_days) > 1:
        actual_start_date = trade_days[0].strftime('%Y-%m-%d')
    else:
        # 如果交易日数据不足，使用原始日期作为起始日期
        actual_start_date = start_date

    return actual_start_date


def mark_key_klines(security, start_date, end_date, frequency='1d', debug=False):
    """
    标记关键K线：小阴小阳、十字星、B1

    参数：
        security: str, 股票代码
        start_date: str, 起始日期 (格式: 'YYYY-MM-DD') - 用户期望的数据起始时间
        end_date: str, 结束日期 (格式: 'YYYY-MM-DD')
        frequency: str, K线周期，可选值: '1d', '1w', '1m', '3m', '6m', '1y'，默认为'1d'
        debug: bool, 是否打印B1标记的调试信息，默认为False
    返回：
        DataFrame: index为交易时间，columns为['股票代码', '小阴小阳', '十字星', 'B1']
                 结果只包含用户期望的起始日期到结束日期范围内的数据
    """
    # 动态计算获取数据所需的实际起始日期
    # 考虑各技术指标计算所需的历史数据长度（MA114需要114个交易日）
    # 从用户输入的起始日期向前扩展至少114个交易日
    actual_start_date = calculate_required_start_date(start_date, frequency)

    # 使用股票数据缓存池获取股票日线数据（前复权）
    df = get_stock_data_with_cache(
        stock_code=security,
        start_date=actual_start_date,
        end_date=end_date
    )

    if df.empty:
        return pd.DataFrame(columns=['股票代码', '小阴小阳', '十字星', 'B1'])

    # 按K线周期进行聚合
    df_resampled = resample_kline(df, frequency)

    # 计算技术指标
    indicators = calculate_kline_indicators(df_resampled)

    # 标记小阴小阳
    small_yang_yin = check_small_yang_yin(df_resampled, indicators)

    # 标记十字星
    doji = check_doji(df_resampled, small_yang_yin)

    # 标记B1（传入debug参数控制是否打印调试信息）
    b1 = check_b1(df_resampled, indicators, small_yang_yin, debug=debug)

    # 构造结果DataFrame，增加股票代码列
    result = pd.DataFrame({
        '股票代码': security,
        '小阴小阳': small_yang_yin,
        '十字星': doji,
        'B1': b1
    }, index=df_resampled.index)

    # 过滤结果，只返回用户期望的时间范围
    result = result.loc[result.index >= pd.Timestamp(start_date)]

    return result



def filter_stocks(concept_code, end_date=None, count=None, start_date=None, frequency='1d', debug=False):
    """
    选择概念板块内符合B1的股票

    参数：
        concept_code: str, 概念板块代码，如 'SC0084'
        end_date: str, 结束日期 (格式: 'YYYY-MM-DD')，默认为当前日期
        count: int, 数据量，与 start_date 二选一，不可同时使用，必须大于0
               表示返回结束日期之前count个交易数据，包含结束日期
        start_date: str, 起始日期 (格式: 'YYYY-MM-DD')，与 count 二选一
        frequency: str, K线周期，可选值: '1d', '1w', '1m', '3m', '6m', '1y'，默认为'1d'
        debug: bool, 是否打印调试信息，默认为False

    返回：
        DataFrame: 包含符合B1条件的股票信息，columns为['股票代码', '最近一次B1时间', 'B1出现次数']
    """
    # 验证参数：count和start_date不可同时使用
    if count is not None and start_date is not None:
        raise ValueError("count和start_date参数不可同时使用，请只提供其中一个")

    # 验证count必须大于0
    if count is not None and count <= 0:
        raise ValueError("count参数必须大于0")

    # 设置默认结束日期为今天
    if end_date is None:
        end_date = dt.today().strftime('%Y-%m-%d')

    # 根据数据量动态计算起始日期
    if count is not None:
        # 根据K线周期计算所需交易日数量
        freq_days = {
            '1d': 1,
            '1w': 5,
            '1m': 20,
            '3m': 60,
            '6m': 120,
            '1y': 240
        }
        days_needed = count * freq_days.get(frequency, 1)
        # 只考虑count计算所需的天数，不在此处考虑技术指标所需的历史数据
        # 技术指标所需的114天在mark_key_klines函数中已实现
        end_dt = dt.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=int(days_needed * 1.5))  # 乘以1.5考虑非交易日
        start_date = start_dt.strftime('%Y-%m-%d')
    elif start_date is None:
        raise ValueError("必须提供 start_date 或 count 参数之一")

    # 获取概念板块内的所有股票
    concept_stocks = get_concept_stocks(concept_code, date=end_date)

    if not concept_stocks:
        print(f"概念板块 {concept_code} 没有获取到股票")
        return []

    # 使用向量化操作过滤股票，减少API调用
    # 先用字符串操作过滤代码前缀（避免调用API）
    concept_stocks_series = pd.Series(concept_stocks)
    # 过滤创业板 (30开头) 和 北交所 (8开头或4开头)
    code_filter_mask = ~concept_stocks_series.str.startswith('300') & \
                       ~concept_stocks_series.str.startswith('301') & \
                       ~concept_stocks_series.str.startswith('8') & \
                       ~concept_stocks_series.str.startswith('4')
    filtered_by_code = concept_stocks_series[code_filter_mask].tolist()

    # 对于剩余股票，只对代码前缀无法判断的（如ST），获取一次所有股票信息进行过滤
    if filtered_by_code:
        # 批量获取剩余股票的名称信息（通过get_all_securities获取所有股票信息）
        all_stocks = get_all_securities(types=['stock'])

        # 创建过滤后的股票集合
        filtered_set = set(filtered_by_code)
        # 获取这些股票的名称信息
        filtered_with_info = all_stocks[all_stocks.index.isin(filtered_set)]

        # 过滤ST股票（使用display_name字段）
        non_st_mask = ~filtered_with_info['display_name'].str.contains('ST|\*ST', na=False)
        filtered_stocks = filtered_with_info[non_st_mask].index.tolist()
    else:
        filtered_stocks = []

    print(f"概念板块 {concept_code} 共有 {len(concept_stocks)} 只股票，过滤后剩余 {len(filtered_stocks)} 只")

    # 遍历所有股票，找出符合B1条件的
    b1_stocks_data = []

    for stock_code in filtered_stocks:
        try:
            # 调用标记关键K线函数
            result = mark_key_klines(stock_code, start_date, end_date, frequency, debug=debug)

            # 检查是否有B1标记
            if result['B1'].any():
                # 获取B1标记的所有行
                b1_rows = result[result['B1']]
                # 获取最后一个B1出现的日期
                last_b1_date = b1_rows.index[-1]
                # 统计B1出现的次数
                b1_count = len(b1_rows)

                b1_stocks_data.append({
                    '股票代码': stock_code,
                    '最近一次B1时间': last_b1_date.strftime('%Y-%m-%d'),
                    'B1出现次数': b1_count
                })

                if debug:
                    print(f"发现B1股票: {stock_code} - "
                          f"最后B1日期: {last_b1_date.strftime('%Y-%m-%d')}, "
                          f"B1次数: {b1_count}")
        except Exception as e:
            if debug:
                print(f"处理股票 {stock_code} 时出错: {str(e)}")
            continue

    print(f"\n共找到 {len(b1_stocks_data)} 只符合B1条件的股票")

    # 返回DataFrame
    if b1_stocks_data:
        return pd.DataFrame(b1_stocks_data, index=None)[['股票代码', '最近一次B1时间', 'B1出现次数']]
    else:
        return pd.DataFrame(columns=['股票代码', '最近一次B1时间', 'B1出现次数'])


def batch_filter_stocks(concept_names, end_date=None, count=None, start_date=None, frequency='1d', debug=False):
    """
    批量查询多个概念板块中符合B1的股票

    参数：
        concept_names: str, 板块名称或关键字，多个板块用'|'分隔，如 '风电|光伏'
        end_date: str, 结束日期 (格式: 'YYYY-MM-DD')，默认为当前日期
        count: int, 数据量，与 start_date 二选一，不可同时使用，必须大于0
        start_date: str, 起始日期 (格式: 'YYYY-MM-DD')，与 count 二选一
        frequency: str, K线周期，可选值: '1d', '1w', '1m', '3m', '6m', '1y'，默认为'1d'
        debug: bool, 是否打印调试信息，默认为False

    返回：
        Tuple(DataFrame, dict): 返回符合B1条件的股票信息和股票的B1标记数据
            - 符合B1的信息汇总: DataFrame, columns为['股票代码', '最近一次B1时间', 'B1出现次数', '涉及的板块']
            - 股票的B1标记数据: dict, key为股票代码，value为该股票的B1标记DataFrame
    """
    # 设置默认结束日期为今天
    if end_date is None:
        end_date = dt.today().strftime('%Y-%m-%d')

    # 解析板块名称列表
    name_list = [name.strip() for name in concept_names.split('|') if name.strip()]

    if not name_list:
        raise ValueError("必须提供有效的板块名称")

    print(f"开始批量查询板块: {concept_names}")
    print(f"时间范围: {start_date or f'最近{count}个周期'} 至 {end_date}")
    print(f"K线周期: {frequency}")
    print("="*80)

    # 获取所有概念板块
    all_concepts = get_concepts()

    # 匹配板块代码（只支持精准匹配）
    concept_code_map = {}  # 板块代码 -> 板块名称
    for name in name_list:
        # 精确匹配
        matched = all_concepts[all_concepts['name'] == name]
        if not matched.empty:
            concept_code = matched.index[0]
            concept_code_map[concept_code] = name
        else:
            print(f"警告: 未找到匹配'{name}'的板块")

    if not concept_code_map:
        print("错误: 没有找到匹配的板块")
        return pd.DataFrame(columns=['股票代码', '最近一次B1时间', 'B1出现次数', '涉及的板块']), {}

    print(f"共匹配到 {len(concept_code_map)} 个板块")
    print("="*80)

    # 用于存储所有股票的结果（去重）
    stock_results = {}  # 股票代码 -> {'股票代码': xxx, '最近一次B1时间': xxx, 'B1出现次数': xxx, '涉及的板块': xxx}
    # 用于存储股票的B1标记数据
    stock_b1_data = {}  # 股票代码 -> DataFrame(B1标记数据)

    # 遍历每个板块，调用filter_stocks
    for concept_code, concept_name in concept_code_map.items():
        print(f"\n查询板块: {concept_name} ({concept_code})")

        try:
            # 调用单板块查询函数
            result_df = filter_stocks(
                concept_code=concept_code,
                end_date=end_date,
                count=count,
                start_date=start_date,
                frequency=frequency,
                debug=debug
            )

            if not result_df.empty:
                # 合并结果
                for idx, row in result_df.iterrows():
                    stock_code = row['股票代码']
                    b1_time = row['最近一次B1时间']
                    b1_count = row['B1出现次数']

                    if stock_code in stock_results:
                        # 股票已存在，更新涉及的板块
                        existing = stock_results[stock_code]
                        # 合并涉及的板块名称
                        existing_sectors = existing['涉及的板块'].split('|')
                        if concept_name not in existing_sectors:
                            existing_sectors.append(concept_name)
                            stock_results[stock_code]['涉及的板块'] = '|'.join(existing_sectors)

                        # 更新B1时间（取最新的）
                        if b1_time > existing['最近一次B1时间']:
                            stock_results[stock_code]['最近一次B1时间'] = b1_time

                        # 累加B1出现次数
                        stock_results[stock_code]['B1出现次数'] += b1_count
                    else:
                        # 新股票
                        stock_results[stock_code] = {
                            '股票代码': stock_code,
                            '最近一次B1时间': b1_time,
                            'B1出现次数': b1_count,
                            '涉及的板块': concept_name
                        }

                    # 获取该股票的B1标记数据
                    try:
                        b1_detail = mark_key_klines(stock_code, start_date, end_date, frequency, debug=False)
                        if not b1_detail.empty:
                            stock_b1_data[stock_code] = b1_detail
                    except Exception as e:
                        if debug:
                            print(f"获取股票 {stock_code} 的B1标记数据时出错: {str(e)}")
                        continue
        except Exception as e:
            print(f"查询板块 {concept_name} 时出错: {str(e)}")
            continue

    # 转换为DataFrame
    if stock_results:
        result_df = pd.DataFrame(list(stock_results.values()), index=None)

        # 按最近一次B1时间降序排序
        result_df = result_df.sort_values(by='最近一次B1时间', ascending=False).reset_index(drop=True)

        print(f"\n{'='*80}")
        print(f"批量查询完成，共找到 {len(result_df)} 只符合B1条件的股票")
        print(f"{'='*80}")

        return result_df, stock_b1_data
    else:
        print(f"\n{'='*80}")
        print("批量查询完成，未找到符合B1条件的股票")
        print(f"{'='*80}")

        return pd.DataFrame(columns=['股票代码', '最近一次B1时间', 'B1出现次数', '涉及的板块']), {}


def load_custom_stocks_config():
    """
    加载自选股配置文件

    返回：
        dict: 自选股配置字典，格式为 {'组名': ['股票代码1', '股票代码2', ...]}
              如果配置文件不存在，则创建默认配置文件并返回空字典
    """
    import os
    import json

    # 获取配置文件路径（始终以脚本所在目录为基准）
    try:
        # 脚本环境：获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # Jupyter Notebook环境：从模块对象获取路径
        try:
            import inspect
            current_dir = os.path.dirname(os.path.abspath(inspect.getfile(load_custom_stocks_config)))
        except (NameError, TypeError):
            # 如果都无法获取，提示用户需要指定路径
            raise ImportError(
                "无法自动确定配置文件路径。在Jupyter Notebook环境中，"
                "请先执行以下代码指定路径：\n"
                "import os\n"
                "os.chdir('d:/Stocks/策略/聚宽选股')\n"
                "或者在调用函数时确保当前工作目录在聚宽选股目录下。"
            )

    config_dir = os.path.join(current_dir, 'config')
    config_file = os.path.join(config_dir, 'stocks_pool.json')

    # 如果config目录不存在，创建它
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"已创建配置目录: {config_dir}")

    # 如果配置文件不存在，创建默认配置文件
    if not os.path.exists(config_file):
        default_config = {
            "说明": "自选股配置文件，按组别管理股票代码",
            "格式": {
                "组名1": ["股票代码1", "股票代码2"],
                "组名2": ["股票代码3", "股票代码4"]
            },
            "示例": {
                "新能源": ["300750.XSHE", "601012.XSHG"],
                "医疗": "000001.XSHE",
                "科技": ["002594.XSHE", "300760.XSHE"]
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

        print(f"已创建默认配置文件: {config_file}")
        print("请在配置文件中添加您的自选股组别和股票代码")
        print("\n配置文件示例：")
        print(json.dumps(default_config, ensure_ascii=False, indent=2))
        return {}

    # 读取配置文件
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 过滤掉说明性字段（非组别字段）
        stocks_config = {}
        for key, value in config.items():
            # 跳过说明性字段
            if key in ['说明', '格式', '示例', '_comment', '_description']:
                continue

            # 确保值是列表或单个字符串
            if isinstance(value, str):
                stock_list = [value]
            elif isinstance(value, list):
                stock_list = value
            else:
                print(f"警告: 组别 '{key}' 的配置格式不正确，已跳过")
                continue

            # 使用 normalize_code 将股票代码转换为聚宽标准格式
            try:
                normalized_codes = normalize_code(stock_list)
                # 确保结果是列表
                if isinstance(normalized_codes, str):
                    normalized_codes = [normalized_codes]
                # 去重
                stocks_config[key] = list(dict.fromkeys(normalized_codes))
            except Exception as e:
                print(f"警告: 转换组别 '{key}' 的股票代码时出错: {str(e)}, 已跳过该组别")
                continue

        return stocks_config
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return {}


def filter_custom_stocks(group_names, end_date=None, count=None, start_date=None, frequency='1d', debug=False):
    """
    批量查询自选股票池中符合B1的股票

    参数：
        group_names: str, 自选股组别名，多个组别名用'|'分隔
        end_date: str, 结束日期 (格式: 'YYYY-MM-DD')，默认为当前日期
        count: int, 数据量，与 start_date 二选一，不可同时使用，必须大于0
               表示返回结束日期之前count个交易数据，包含结束日期
        start_date: str, 起始日期 (格式: 'YYYY-MM-DD')，与 count 二选一
        frequency: str, K线周期，可选值: '1d', '1w', '1m', '3m', '6m', '1y'，默认为'1d'
        debug: bool, 是否打印调试信息，默认为False

    返回：
        Tuple(DataFrame, dict): 返回符合B1条件的股票信息和股票的B1标记数据
            - 符合B1的信息汇总: DataFrame, columns为['股票代码', '最近一次B1时间', 'B1出现次数', '涉及的自选组']
            - 股票的B1标记数据: dict, key为股票代码，value为该股票的B1标记DataFrame
    """
    # 验证参数：count和start_date不可同时使用
    if count is not None and start_date is not None:
        raise ValueError("count和start_date参数不可同时使用，请只提供其中一个")

    # 验证count必须大于0
    if count is not None and count <= 0:
        raise ValueError("count参数必须大于0")

    # 设置默认结束日期为今天
    if end_date is None:
        end_date = dt.today().strftime('%Y-%m-%d')

    # 根据数据量动态计算起始日期
    if count is not None:
        # 根据K线周期计算所需交易日数量
        freq_days = {
            '1d': 1,
            '1w': 5,
            '1m': 20,
            '3m': 60,
            '6m': 120,
            '1y': 240
        }
        days_needed = count * freq_days.get(frequency, 1)
        # 只考虑count计算所需的天数，不在此处考虑技术指标所需的历史数据
        # 技术指标所需的114天在mark_key_klines函数中已实现
        end_dt = dt.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=int(days_needed * 1.5))  # 乘以1.5考虑非交易日
        start_date = start_dt.strftime('%Y-%m-%d')
    elif start_date is None:
        raise ValueError("必须提供 start_date 或 count 参数之一")

    # 加载自选股配置
    stocks_config = load_custom_stocks_config()

    if not stocks_config:
        print("错误: 自选股配置为空或配置文件不存在")
        return pd.DataFrame(columns=['股票代码', '最近一次B1时间', 'B1出现次数', '涉及的自选组']), {}

    # 解析组别名列表
    group_list = [name.strip() for name in group_names.split('|') if name.strip()]

    if not group_list:
        raise ValueError("必须提供有效的组别名")

    print(f"开始查询自选股组: {group_names}")
    print(f"时间范围: {start_date or f'最近{count}个周期'} 至 {end_date}")
    print(f"K线周期: {frequency}")
    print("="*80)

    # 收集所有要查询的股票及其所属组别
    stock_groups = {}  # 股票代码 -> 组别名列表
    matched_groups = {}  # 组别名 -> 股票列表

    for group_name in group_list:
        if group_name in stocks_config:
            stocks = stocks_config[group_name]
            if stocks:
                matched_groups[group_name] = stocks
                print(f"组别 '{group_name}': 共 {len(stocks)} 只股票")

                for stock_code in stocks:
                    if stock_code not in stock_groups:
                        stock_groups[stock_code] = []
                    stock_groups[stock_code].append(group_name)
            else:
                print(f"警告: 组别 '{group_name}' 下没有股票")
        else:
            print(f"警告: 未找到组别 '{group_name}'")

    if not matched_groups:
        print("错误: 没有匹配到任何有效的自选股组别")
        return pd.DataFrame(columns=['股票代码', '最近一次B1时间', 'B1出现次数', '涉及的自选组']), {}

    print(f"共匹配到 {len(matched_groups)} 个组别，总计 {len(stock_groups)} 只股票")
    print("="*80)

    # 用于存储所有股票的结果
    stock_results = {}  # 股票代码 -> {'股票代码': xxx, '最近一次B1时间': xxx, 'B1出现次数': xxx, '涉及的自选组': xxx}
    # 用于存储股票的B1标记数据
    stock_b1_data = {}  # 股票代码 -> DataFrame(B1标记数据)

    # 遍历所有股票，找出符合B1条件的
    for stock_code, group_list in stock_groups.items():
        try:
            # 调用标记关键K线函数
            result = mark_key_klines(stock_code, start_date, end_date, frequency, debug=debug)

            # 检查是否有B1标记
            if result['B1'].any():
                # 获取B1标记的所有行
                b1_rows = result[result['B1']]
                # 获取最后一个B1出现的日期
                last_b1_date = b1_rows.index[-1]
                # 统计B1出现的次数
                b1_count = len(b1_rows)

                stock_results[stock_code] = {
                    '股票代码': stock_code,
                    '最近一次B1时间': last_b1_date.strftime('%Y-%m-%d'),
                    'B1出现次数': b1_count,
                    '涉及的自选组': '|'.join(group_list)
                }

                # 保存B1标记数据
                stock_b1_data[stock_code] = result

                if debug:
                    print(f"发现B1股票: {stock_code} - "
                          f"最后B1日期: {last_b1_date.strftime('%Y-%m-%d')}, "
                          f"B1次数: {b1_count}, "
                          f"涉及组: {'|'.join(group_list)}")
        except Exception as e:
            if debug:
                print(f"处理股票 {stock_code} 时出错: {str(e)}")
            continue

    # 转换为DataFrame
    if stock_results:
        result_df = pd.DataFrame(list(stock_results.values()), index=None)

        # 确保列顺序
        result_df = result_df[['股票代码', '最近一次B1时间', 'B1出现次数', '涉及的自选组']]

        # 按最近一次B1时间降序排序
        result_df = result_df.sort_values(by='最近一次B1时间', ascending=False).reset_index(drop=True)

        print(f"\n{'='*80}")
        print(f"自选股查询完成，共找到 {len(result_df)} 只符合B1条件的股票")
        print(f"{'='*80}")

        return result_df, stock_b1_data
    else:
        print(f"\n{'='*80}")
        print("自选股查询完成，未找到符合B1条件的股票")
        print(f"{'='*80}")

        return pd.DataFrame(columns=['股票代码', '最近一次B1时间', 'B1出现次数', '涉及的自选组']), {}


def full_scan_b1_stocks(end_date=None, count=None, start_date=None, frequency='1d', debug=False):
    """
    全量扫描符合B1的股票

    参数：
        end_date: str, 结束日期 (格式: 'YYYY-MM-DD')，默认为当前日期
        count: int, 数据量，与 start_date 二选一，不可同时使用，必须大于0
               表示返回结束日期之前count个交易数据，包含结束日期
        start_date: str, 起始日期 (格式: 'YYYY-MM-DD')，与 count 二选一
        frequency: str, K线周期，可选值: '1d', '1w', '1m', '3m', '6m', '1y'，默认为'1d'
        debug: bool, 是否打印调试信息，默认为False

    返回：
        Tuple(DataFrame, dict): 返回符合B1条件的股票信息和股票的B1标记数据
            - 符合B1的信息汇总: DataFrame, columns为['股票代码', '最近一次B1时间', 'B1出现次数']
            - 股票的B1标记数据: dict, key为股票代码，value为该股票的B1标记DataFrame
    """
    # 验证参数：count和start_date不可同时使用
    if count is not None and start_date is not None:
        raise ValueError("count和start_date参数不可同时使用，请只提供其中一个")

    # 验证count必须大于0
    if count is not None and count <= 0:
        raise ValueError("count参数必须大于0")

    # 设置默认结束日期为今天
    if end_date is None:
        end_date = dt.today().strftime('%Y-%m-%d')

    # 根据数据量动态计算起始日期
    if count is not None:
        # 根据K线周期计算所需交易日数量
        freq_days = {
            '1d': 1,
            '1w': 5,
            '1m': 20,
            '3m': 60,
            '6m': 120,
            '1y': 240
        }
        days_needed = count * freq_days.get(frequency, 1)
        # 只考虑count计算所需的天数，不在此处考虑技术指标所需的历史数据
        # 技术指标所需的114天在mark_key_klines函数中已实现
        end_dt = dt.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=int(days_needed * 1.5))  # 乘以1.5考虑非交易日
        start_date = start_dt.strftime('%Y-%m-%d')
    elif start_date is None:
        raise ValueError("必须提供 start_date 或 count 参数之一")

    print(f"开始全量扫描符合B1的股票")
    print(f"时间范围: {start_date or f'最近{count}个周期'} 至 {end_date}")
    print(f"K线周期: {frequency}")
    print("="*80)

    # 获取所有股票代码（包含名称信息）
    all_stocks = get_all_securities(types=['stock'])

    if all_stocks is None or all_stocks.empty:
        print("错误: 未获取到股票列表")
        return pd.DataFrame(columns=['股票代码', '最近一次B1时间', 'B1出现次数']), {}

    # 使用DataFrame向量化操作过滤股票，避免逐个调用get_security_info
    # 1. 过滤ST股票（使用display_name字段）
    non_st_mask = ~all_stocks['display_name'].str.contains('ST|\*ST', na=False)

    # 2. 过滤创业板 (30开头) 和 北交所 (8开头或4开头)
    # 股票代码格式为：000001.XSHE（深市）或 600000.XSHG（沪市）
    # 提取6位数字代码（取前6位）
    stock_codes = all_stocks.index.str[:6]

    non_300_mask = ~stock_codes.str.startswith('300') & ~stock_codes.str.startswith('301')
    non_bse_mask = ~stock_codes.str.startswith('8') & ~stock_codes.str.startswith('4')

    # 3. 组合所有过滤条件
    filter_mask = non_st_mask & non_300_mask & non_bse_mask

    # 4. 应用过滤
    filtered_stocks = all_stocks[filter_mask].index.tolist()

    print(f"全市场共有 {len(all_stocks)} 只股票，过滤后剩余 {len(filtered_stocks)} 只")
    print("="*80)

    # 遍历所有股票，找出符合B1条件的
    b1_stocks_data = []
    processed_count = 0
    stock_b1_data = {}  # 股票代码 -> DataFrame(B1标记数据)

    for stock_code in filtered_stocks:
        try:
            # 调用标记关键K线函数
            result = mark_key_klines(stock_code, start_date, end_date, frequency, debug=debug)

            # 检查是否有B1标记
            if result['B1'].any():
                # 获取B1标记的所有行
                b1_rows = result[result['B1']]
                # 获取最后一个B1出现的日期
                last_b1_date = b1_rows.index[-1]
                # 统计B1出现的次数
                b1_count = len(b1_rows)

                b1_stocks_data.append({
                    '股票代码': stock_code,
                    '最近一次B1时间': last_b1_date.strftime('%Y-%m-%d'),
                    'B1出现次数': b1_count
                })

                # 保存B1标记数据
                stock_b1_data[stock_code] = result

                if debug:
                    print(f"发现B1股票: {stock_code} - "
                          f"最后B1日期: {last_b1_date.strftime('%Y-%m-%d')}, "
                          f"B1次数: {b1_count}")

            processed_count += 1
            # 每处理100只股票打印一次进度
            if processed_count % 100 == 0:
                print(f"已处理 {processed_count}/{len(filtered_stocks)} 只股票...")
        except Exception as e:
            if debug:
                print(f"处理股票 {stock_code} 时出错: {str(e)}")
            continue

    print(f"\n{'='*80}")
    print(f"全量扫描完成，共找到 {len(b1_stocks_data)} 只符合B1条件的股票")
    print(f"{'='*80}")

    # 返回Tuple
    if b1_stocks_data:
        result_df = pd.DataFrame(b1_stocks_data, index=None)
        # 确保列顺序
        result_df = result_df[['股票代码', '最近一次B1时间', 'B1出现次数']]
        # 按最近一次B1时间降序排序
        result_df = result_df.sort_values(by='最近一次B1时间', ascending=False).reset_index(drop=True)
        return result_df, stock_b1_data
    else:
        return pd.DataFrame(columns=['股票代码', '最近一次B1时间', 'B1出现次数']), {}


def calculate_concept_potential(b1_stocks_data=None, concept_names=None, group_names=None, end_date=None, count=None, start_date=None, frequency='1d', debug=False):
    """
    根据股票的B1标记数据，统计概念板块B1出现的情况

    参数：
        b1_stocks_data: DataFrame, 符合B1的股票数据，columns为['股票代码', '最近一次B1时间', 'B1出现次数']
                        如果为None，则根据其他参数获取B1数据
        concept_names: str, 板块名称，多个板块用'|'分隔，如 '风电|光伏'
                        只能精确查找，不支持模糊查找，默认为None
        group_names: str, 自选股组别名，多个组别名用'|'分隔
                        只能精确查找，不支持模糊查找，默认为None
        end_date: str, 结束日期 (格式: 'YYYY-MM-DD')，默认为当前日期
        count: int, 数据量，与 start_date 二选一，不可同时使用，必须大于0
               表示返回结束日期之前count个交易数据，包含结束日期
        start_date: str, 起始日期 (格式: 'YYYY-MM-DD')，与 count 二选一
        frequency: str, K线周期，可选值: '1d', '1w', '1m', '3m', '6m', '1y'，默认为'1d'
        debug: bool, 是否打印调试信息，默认为False

    返回：
        Tuple(DataFrame, DataFrame): 返回概念板块统计和交易日统计两个DataFrame
            - 概念板块统计：columns为['板块代码', '板块名称', '出现B1的股票数量', 'B1出现的总次数']
            - 交易日统计：columns为['交易日期', 'B1出现的次数']
    """
    # 验证参数：count和start_date不可同时使用
    if count is not None and start_date is not None:
        raise ValueError("count和start_date参数不可同时使用，请只提供其中一个")

    # 验证count必须大于0
    if count is not None and count <= 0:
        raise ValueError("count参数必须大于0")

    # 设置默认结束日期为今天
    if end_date is None:
        end_date = dt.today().strftime('%Y-%m-%d')

    # 根据数据量动态计算起始日期
    if count is not None:
        # 根据K线周期计算所需交易日数量
        freq_days = {
            '1d': 1,
            '1w': 5,
            '1m': 20,
            '3m': 60,
            '6m': 120,
            '1y': 240
        }
        days_needed = count * freq_days.get(frequency, 1)
        # 只考虑count计算所需的天数，不在此处考虑技术指标所需的历史数据
        # 技术指标所需的114天在mark_key_klines函数中已实现
        end_dt = dt.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=int(days_needed * 1.5))  # 乘以1.5考虑非交易日
        start_date = start_dt.strftime('%Y-%m-%d')
    elif start_date is None:
        raise ValueError("必须提供 start_date 或 count 参数之一")

    print(f"开始统计概念板块B1出现情况")
    print(f"时间范围: {start_date or f'最近{count}个周期'} 至 {end_date}")
    print(f"K线周期: {frequency}")
    print("="*80)

    # 获取B1股票数据（根据不同使用方式）
    # 方式1: 直接使用提供的b1_stocks_data (格式为DataFrame或tuple)
    # 方式2: 根据concept_names调用batch_filter_stocks
    # 方式3: 根据group_names调用filter_custom_stocks
    # 方式4: 调用full_scan_b1_stocks进行全量扫描
    stock_b1_data_dict = {}  # 用于存储股票的B1标记数据

    if b1_stocks_data is None:
        if concept_names is not None:
            # 方式2: 根据板块名获取B1数据
            print(f"使用方式2：根据板块名 '{concept_names}' 获取B1股票数据...")
            b1_stocks_data, stock_b1_data_dict = batch_filter_stocks(
                concept_names=concept_names,
                end_date=end_date,
                count=count,
                start_date=start_date,
                frequency=frequency,
                debug=debug
            )
        elif group_names is not None:
            # 方式3: 根据组别名获取B1数据
            print(f"使用方式3：根据组别名 '{group_names}' 获取B1股票数据...")
            b1_stocks_data, stock_b1_data_dict = filter_custom_stocks(
                group_names=group_names,
                end_date=end_date,
                count=count,
                start_date=start_date,
                frequency=frequency,
                debug=debug
            )
        else:
            # 方式4: 全量扫描
            print("使用方式4：全量扫描获取B1股票数据...")
            b1_stocks_data, stock_b1_data_dict = full_scan_b1_stocks(
                end_date=end_date,
                count=count,
                start_date=start_date,
                frequency=frequency,
                debug=debug
            )
        print("="*80)
    else:
        # 方式1: 直接使用提供的B1数据
        print("使用方式1：直接使用提供的B1股票数据")
        # 如果b1_stocks_data是DataFrame，需要获取详细的B1标记数据

    # 初始化结果DataFrame
    concept_stats_df = pd.DataFrame(columns=['板块代码', '板块名称', '出现B1的股票数量', 'B1出现的总次数'])
    trading_day_stats_df = pd.DataFrame(columns=['交易日期', 'B1出现的次数'])

    # 如果没有B1股票数据，返回空结果
    if b1_stocks_data is None or b1_stocks_data.empty:
        print("未找到符合B1条件的股票")
        return concept_stats_df, trading_day_stats_df

    print(f"已加载 {len(b1_stocks_data)} 只符合B1条件的股票数据")

    # 用于存储每只股票的B1信息（需要包含所有B1出现的日期）
    stock_b1_detail_info = {}  # 股票代码 -> {'B1次数': xxx, 'B1日期列表': [date1, date2, ...]}

    # 获取详细的B1标记数据
    print("开始获取B1股票的详细标记数据...")

    if stock_b1_data_dict:
        # 使用已有的B1标记数据
        for stock_code, b1_df in stock_b1_data_dict.items():
            if not b1_df.empty and 'B1' in b1_df.columns:
                b1_dates = b1_df[b1_df['B1'] == True].index.tolist()
                stock_b1_detail_info[stock_code] = {
                    'B1次数': len(b1_dates),
                    'B1日期列表': b1_dates
                }
    else:
        # 重新获取详细的B1标记数据
        for idx, row in b1_stocks_data.iterrows():
            stock_code = row['股票代码']
            try:
                # 调用mark_key_klines获取详细的B1标记
                kline_result = mark_key_klines(stock_code, start_date, end_date, frequency, debug=False)

                # 提取所有B1标记的日期
                if 'B1' in kline_result.columns:
                    b1_dates = kline_result[kline_result['B1'] == True].index.tolist()
                    stock_b1_detail_info[stock_code] = {
                        'B1次数': len(b1_dates),
                        'B1日期列表': b1_dates
                    }
            except Exception as e:
                if debug:
                    print(f"获取股票 {stock_code} 的B1详细标记时出错: {str(e)}")
                continue

    print(f"成功获取 {len(stock_b1_detail_info)} 只股票的B1详细标记数据")
    print("="*80)

    # 1. 统计概念板块数据
    print("开始统计概念板块数据...")
    concept_data = {}  # 板块代码 -> {'板块名称': xxx, '出现B1的股票数量': xxx, 'B1出现的总次数': xxx}

    # 遍历所有股票，统计每个概念板块的B1情况
    for stock_code, b1_info in stock_b1_detail_info.items():
        try:
            # 获取股票所属的所有概念板块
            stock_concepts = get_concept(security=stock_code, date=end_date)

            if stock_concepts and stock_code in stock_concepts:
                # 聚宽概念列表
                jq_concepts = stock_concepts[stock_code].get('jq_concept', [])

                for concept in jq_concepts:
                    concept_code = concept.get('concept_code')
                    concept_name = concept.get('concept_name')

                    if not concept_code:
                        continue

                    # 初始化概念板块数据
                    if concept_code not in concept_data:
                        concept_data[concept_code] = {
                            '板块名称': concept_name,
                            '出现B1的股票数量': 0,
                            'B1出现的总次数': 0
                        }

                    # 更新B1统计数据
                    concept_data[concept_code]['出现B1的股票数量'] += 1
                    concept_data[concept_code]['B1出现的总次数'] += b1_info['B1次数']

        except Exception as e:
            if debug:
                print(f"处理股票 {stock_code} 的概念板块时出错: {str(e)}")
            continue

    # 构造概念板块统计DataFrame
    concept_result_data = []
    for concept_code, data in concept_data.items():
        concept_result_data.append({
            '板块代码': concept_code,
            '板块名称': data['板块名称'],
            '出现B1的股票数量': data['出现B1的股票数量'],
            'B1出现的总次数': data['B1出现的总次数']
        })

    if concept_result_data:
        concept_stats_df = pd.DataFrame(concept_result_data, index=None)
        # 确保列顺序
        concept_stats_df = concept_stats_df[['板块代码', '板块名称', '出现B1的股票数量', 'B1出现的总次数']]
        # 按B1出现的总次数降序排序
        concept_stats_df = concept_stats_df.sort_values(by='B1出现的总次数', ascending=False).reset_index(drop=True)

    print(f"\n{'='*80}")
    print(f"概念板块统计完成，共分析 {len(concept_data)} 个概念板块")
    print(f"{'='*80}")

    # 2. 统计交易日数据
    print("开始统计交易日B1出现情况...")
    trading_day_count = {}  # 交易日期 -> B1出现次数

    for stock_code, b1_info in stock_b1_detail_info.items():
        for b1_date in b1_info['B1日期列表']:
            # 将日期转换为字符串格式
            date_str = b1_date.strftime('%Y-%m-%d')
            trading_day_count[date_str] = trading_day_count.get(date_str, 0) + 1

    # 构造交易日统计DataFrame
    trading_day_result_data = []
    for date_str, count in sorted(trading_day_count.items(), reverse=True):
        trading_day_result_data.append({
            '交易日期': date_str,
            'B1出现的次数': count
        })

    if trading_day_result_data:
        trading_day_stats_df = pd.DataFrame(trading_day_result_data, index=None)
        # 确保列顺序
        trading_day_stats_df = trading_day_stats_df[['交易日期', 'B1出现的次数']]

    print(f"交易日统计完成，共 {len(trading_day_count)} 个交易日出现B1")
    print(f"{'='*80}")

    return concept_stats_df, trading_day_stats_df


def main():
    """
    主函数：演示如何使用mark_key_klines函数和filter_stocks函数
    """
    print("="*80)
    print("示例1：标记单只股票的关键K线")
    print("="*80)

    # 示例：标记平安银行的关键K线
    security = '000001.XSHE'
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    frequency = '1d'

    # 启用调试模式，会打印B1标记的详细信息
    debug_mode = False

    result = mark_key_klines(security, start_date, end_date, frequency, debug=debug_mode)

    print(f"\n股票: {security}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"K线周期: {frequency}")
    print("\n关键K线标记结果：")
    print(result[result['B1']])

    # 统计各类型关键K线的数量（排除股票代码列）
    print("\n统计：")
    print(result[['小阴小阳', '十字星', 'B1']].sum())

    print("\n" + "="*80)
    print("示例2：选择概念板块内符合B1的股票")
    print("="*80)

    # 示例：获取风电概念板块内符合B1的股票
    concept_code = 'SC0084'  # 风电概念
    end_date = '2024-12-31'
    count = 20  # 获取最近20个交易日的数据
    frequency = '1d'
    debug_mode = False

    b1_stocks = filter_stocks(
        concept_code=concept_code,
        end_date=end_date,
        count=count,
        frequency=frequency,
        debug=debug_mode
    )

    print(f"\n概念板块 {concept_code} 内符合B1条件的股票信息：")
    print(b1_stocks)

    print("\n" + "="*80)
    print("示例3：批量查询多个概念板块内符合B1的股票")
    print("="*80)

    # 示例：批量查询风电和光伏概念板块内符合B1的股票
    concept_names = '风电|光伏'
    end_date = '2024-12-31'
    count = 30  # 获取最近30个交易日的数据
    frequency = '1d'
    debug_mode = False

    b1_stocks_batch, b1_data_dict_batch = batch_filter_stocks(
        concept_names=concept_names,
        end_date=end_date,
        count=count,
        frequency=frequency,
        debug=debug_mode
    )

    print(f"\n批量查询结果：")
    print(b1_stocks_batch)

    print("\n" + "="*80)
    print("示例4：批量查询自选股票池中符合B1的股票")
    print("="*80)

    # 示例：查询自选股中符合B1的股票
    custom_groups = '新能源|医疗'
    end_date = '2024-12-31'
    count = 20  # 获取最近20个交易日的数据
    frequency = '1d'
    debug_mode = False

    custom_b1_stocks, b1_data_dict_custom = filter_custom_stocks(
        group_names=custom_groups,
        end_date=end_date,
        count=count,
        frequency=frequency,
        debug=debug_mode
    )

    print(f"\n自选股组 {custom_groups} 内符合B1条件的股票信息：")
    print(custom_b1_stocks)

    print("\n" + "="*80)
    print("示例5：全量扫描符合B1的股票")
    print("="*80)

    # 示例：全量扫描所有符合B1的股票
    end_date = '2024-12-31'
    count = 10  # 获取最近10个交易日的数据
    frequency = '1d'
    debug_mode = False

    full_scan_result, b1_data_dict_scan = full_scan_b1_stocks(
        end_date=end_date,
        count=count,
        frequency=frequency,
        debug=debug_mode
    )

    print(f"\n全量扫描结果（前20条）：")
    print(full_scan_result.head(20))

    print("\n" + "="*80)
    print("示例6：统计概念板块B1出现情况")
    print("="*80)

    # 示例6a：不提供B1股票数据，自动进行全量扫描（方式4）
    end_date = '2024-12-31'
    count = 20  # 获取最近20个交易日的数据
    frequency = '1d'
    debug_mode = False

    concept_stats, day_stats = calculate_concept_potential(
        end_date=end_date,
        count=count,
        frequency=frequency,
        debug=debug_mode
    )

    print(f"\n概念板块统计（前30名）：")
    print(concept_stats.head(30))

    print(f"\n交易日统计（前20名）：")
    print(day_stats.head(20))

    # 示例6b：提供已有的B1股票数据（方式1）
    print("\n" + "="*80)
    print("示例6b：使用已有的B1股票数据统计")
    print("="*80)

    # 使用示例5的结果
    if not full_scan_result.empty:
        concept_stats2, day_stats2 = calculate_concept_potential(
            b1_stocks_data=full_scan_result,
            debug=debug_mode
        )

        print(f"\n概念板块统计（前30名）：")
        print(concept_stats2.head(30))

        print(f"\n交易日统计（前20名）：")
        print(day_stats2.head(20))
    else:
        print("示例5结果为空，跳过此示例")

    # 示例6c：根据板块名获取B1数据并统计（方式2）
    print("\n" + "="*80)
    print("示例6c：根据板块名获取B1数据并统计")
    print("="*80)

    concept_names = '风电|光伏'
    count = 30  # 获取最近30个交易日的数据

    concept_stats3, day_stats3 = calculate_concept_potential(
        concept_names=concept_names,
        end_date=end_date,
        count=count,
        frequency=frequency,
        debug=debug_mode
    )

    print(f"\n概念板块统计：")
    print(concept_stats3)

    print(f"\n交易日统计：")
    print(day_stats3)

    # 示例6d：根据组别名获取B1数据并统计（方式3）
    print("\n" + "="*80)
    print("示例6d：根据组别名获取B1数据并统计")
    print("="*80)

    group_names = '新能源|医疗'
    count = 20  # 获取最近20个交易日的数据

    concept_stats4, day_stats4 = calculate_concept_potential(
        group_names=group_names,
        end_date=end_date,
        count=count,
        frequency=frequency,
        debug=debug_mode
    )

    print(f"\n概念板块统计：")
    print(concept_stats4)

    print(f"\n交易日统计：")
    print(day_stats4)


if __name__ == '__main__':
    pass
    # main()
