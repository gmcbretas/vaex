import vaex
import numpy as np
from common import *

# def test_count_multiple_selections():

def test_sum(df, ds_trimmed):
    df.select("x < 5")
    np.testing.assert_array_almost_equal(df.sum("x", selection=None), np.nansum(ds_trimmed.data.x))
    np.testing.assert_array_almost_equal(df.sum("x", selection=True), np.nansum(ds_trimmed.data.x[:5]))
    np.testing.assert_array_almost_equal(df.sum(df.x, selection=None), np.nansum(ds_trimmed.data.x))
    np.testing.assert_array_almost_equal(df.sum(df.x, selection=True), np.nansum(ds_trimmed.data.x[:5]))

    df.select("x > 5")
    np.testing.assert_array_almost_equal(df.sum("m", selection=None), np.nansum(ds_trimmed.data.m))
    np.testing.assert_array_almost_equal(df.sum("m", selection=True), np.nansum(ds_trimmed.data.m[6:]))
    np.testing.assert_array_almost_equal(df.m.sum(selection=True), np.nansum(ds_trimmed.data.m[6:]))

    df.select("x < 5")
    # convert to float
    x = ds_trimmed.columns["x"]
    y = ds_trimmed.data.y
    x_with_nan = x * 1
    x_with_nan[0] = np.nan
    ds_trimmed.columns["x"] = x_with_nan
    np.testing.assert_array_almost_equal(df.sum("x", selection=None), np.nansum(x))
    np.testing.assert_array_almost_equal(df.sum("x", selection=True), np.nansum(x[:5]))

    task = df.sum("x", selection=True, delay=True)
    df.execute()
    np.testing.assert_array_almost_equal(task.get(), np.nansum(x[:5]))


    np.testing.assert_array_almost_equal(df.sum("x", selection=None, binby=["x"], limits=[0, 10], shape=1), [np.nansum(x)])
    np.testing.assert_array_almost_equal(df.sum("x", selection=True, binby=["x"], limits=[0, 10], shape=1), [np.nansum(x[:5])])
    np.testing.assert_array_almost_equal(df.sum("x", selection=None, binby=["y"], limits=[0, 9**2+1], shape=1), [np.nansum(x)])
    np.testing.assert_array_almost_equal(df.sum("x", selection=True, binby=["y"], limits=[0, 9**2+1], shape=1), [np.nansum(x[:5])])
    np.testing.assert_array_almost_equal(df.sum("x", selection=None, binby=["x"], limits=[0, 10], shape=2), [np.nansum(x[:5]), np.nansum(x[5:])])
    np.testing.assert_array_almost_equal(df.sum("x", selection=True, binby=["x"], limits=[0, 10], shape=2), [np.nansum(x[:5]), 0])

    i = 7
    np.testing.assert_array_almost_equal(df.sum("x", selection=None, binby=["y"], limits=[0, 9**2+1], shape=2), [np.nansum(x[:i]), np.nansum(x[i:])])
    np.testing.assert_array_almost_equal(df.sum("x", selection=True, binby=["y"], limits=[0, 9**2+1], shape=2), [np.nansum(x[:5]), 0])

    i = 5
    np.testing.assert_array_almost_equal(df.sum("y", selection=None, binby=["x"], limits=[0, 10], shape=2), [np.nansum(y[:i]), np.nansum(y[i:])])
    np.testing.assert_array_almost_equal(df.sum("y", selection=True, binby=["x"], limits=[0, 10], shape=2), [np.nansum(y[:5]), 0])


def test_count_1d():
    x = np.array([-1, -2, 0.5, 1.5, 4.5, 5], dtype='f8')
    df = vaex.from_arrays(x=x)

    bins = 5
    binner = df._binner_scalar('x', [0, 5], bins)
    grid = vaex.superagg.Grid([binner])
    agg = vaex.agg.count()
    grid = df._agg(agg, grid)
    assert grid.tolist() == [0, 2, 1, 1, 0, 0, 1, 1]

def test_count_types(ds_local):
    df = ds_local
    assert df.count(df.x) is not None
    assert df.count(df.datetime) is not None
    assert df.min(df.datetime) is not None
    assert df.max(df.datetime) is not None
    assert df.minmax(df.datetime) is not None
    assert df.std(df.datetime) is not None


def test_count_1d_ordinal():
    x = np.array([-1, -2, 0, 1, 4, 5], dtype='i8')
    df = vaex.from_arrays(x=x)

    bins = 5
    binner = df._binner_ordinal('x', 5)
    grid = vaex.superagg.Grid([binner])
    agg = vaex.agg.count()
    grid = df._agg(agg, grid)
    assert grid.tolist() == [0, 2, 1, 1, 0, 0, 1, 1]


def test_minmax():
    x = np.arange(1, 10, 1)
    df = vaex.from_arrays(x=x)
    assert df.x.min() == 1
    assert df.x.max() == 9

    assert df[(df.x > 3) & (df.x < 7)]['x'].min() == (4)
    assert df[(df.x > 3) & (df.x < 7)]['x'].max() == (6)

    df = vaex.from_arrays(x=-x)
    assert df.x.max() == -1
    assert df.x.min() == -9


def test_minmax_all_dfs(df):
    vmin, vmax = df.minmax(df.x)
    assert df.min(df.x) == vmin
    assert df.max(df.x) == vmax


def test_big_endian_binning():
    x = np.arange(10, dtype='>f8')
    y = np.zeros(10, dtype='>f8')
    ds = vaex.from_arrays(x=x, y=y)
    counts = ds.count(binby=[ds.x, ds.y], limits=[[-0.5, 9.5], [-0.5, 0.5]], shape=[10, 1])
    assert counts.ravel().tolist() == np.ones(10).tolist()


def test_big_endian_binning_non_contiguous():
    x = np.arange(20, dtype='>f8')[::2]
    x[:] = np.arange(10, dtype='>f8')
    y = np.arange(20, dtype='>f8')[::2]
    y[:] = np.arange(10, dtype='>f8')
    ds = vaex.from_arrays(x=x, y=y)
    counts = ds.count(binby=[ds.x, ds.y], limits=[[-0.5, 9.5], [-0.5, 9.5]], shape=[10, 10])
    assert np.diagonal(counts).tolist() == np.ones(10).tolist()


def test_strides():
    ar = np.zeros((10, 2)).reshape(20)
    x = ar[::2]
    x[:] = np.arange(10)
    ds = vaex.from_arrays(x=x)
    counts = ds.count(binby=ds.x, limits=[-0.5, 9.5], shape=10)
    assert counts.tolist() == np.ones(10).tolist()


def test_expr():
    ar = np.zeros((10, 2)).reshape(20)
    x = ar[::2]
    x[:] = np.arange(10)
    ds = vaex.from_arrays(x=x)
    counts = ds.count('x*2', binby='x*2', limits=[-0.5, 19.5], shape=10)
    assert counts.tolist() == np.ones(10).tolist()


def test_nunique():
    s = ['aap', 'aap', 'noot', 'mies', None, 'mies', 'kees', 'mies', 'aap']
    x = [0,     0,     0,      0,      0,     1,      1,     1,      2]
    df = vaex.from_arrays(x=x, s=s)
    dfg = df.groupby(df.x, agg={'nunique': vaex.agg.nunique(df.s)}).sort(df.x)
    items = list(zip(dfg.x.values, dfg.nunique.values))
    assert items == [(0, 4), (1, 2), (2, 1)]

    dfg = df.groupby(df.x, agg={'nunique': vaex.agg.nunique(df.s, dropmissing=True)}).sort(df.x)
    items = list(zip(dfg.x.values, dfg.nunique.values))
    assert items == [(0, 3), (1, 2), (2, 1)]

    # we just map the strings to floats, to have the same test for floats/primitives
    mapping = {'aap': 1.2, 'noot': 2.5, 'mies': 3.7, 'kees': 4.8, None: np.nan}
    s = np.array([mapping[k] for k in s], dtype=np.float64)
    df = vaex.from_arrays(x=x, s=s)
    dfg = df.groupby(df.x, agg={'nunique': vaex.agg.nunique(df.s)}).sort(df.x)
    items = list(zip(dfg.x.values, dfg.nunique.values))
    assert items == [(0, 4), (1, 2), (2, 1)]

    dfg = df.groupby(df.x, agg={'nunique': vaex.agg.nunique(df.s, dropnan=True)}).sort(df.x)
    items = list(zip(dfg.x.values, dfg.nunique.values))
    assert items == [(0, 3), (1, 2), (2, 1)]


def test_nunique_filtered():
    s = ['aap', 'aap', 'noot', 'mies', None, 'mies', 'kees', 'mies', 'aap']
    x = [0,     0,     0,      0,      0,     1,      1,     1,      2]
    y = [1,     1,     0,      1,      0,     0,      0,     1,      1]
    df = vaex.from_arrays(x=x, s=s, y=y)
    dfg = df[df.y==0].groupby(df.x, agg={'nunique': vaex.agg.nunique(df.s)}).sort(df.x)
    items = list(zip(dfg.x.values, dfg.nunique.values))
    assert items == [(0, 2), (1, 2)]

    # we just map the strings to floats, to have the same test for floats/primitives
    mapping = {'aap': 1.2, 'noot': 2.5, 'mies': 3.7, 'kees': 4.8, None: np.nan}
    s = np.array([mapping[k] for k in s], dtype=np.float64)
    df = vaex.from_arrays(x=x, s=s, y=y)
    dfg = df[df.y==0].groupby(df.x, agg={'nunique': vaex.agg.nunique(df.s)}).sort(df.x)
    items = list(zip(dfg.x.values, dfg.nunique.values))
    assert items == [(0, 2), (1, 2)]


def test_unique_missing_groupby():
    s = ['aap', 'aap', 'noot', 'mies', None, 'mies', 'kees', 'mies', 'aap']
    x = [0,     0,     0,      np.nan,      np.nan,     1,      1,     np.nan,      2]
    df = vaex.from_arrays(x=x, s=s)
    dfg = df.groupby(df.x, agg={'nunique': vaex.agg.nunique(df.s)}).sort(df.x)
    items = list(zip(dfg.x.values, dfg.nunique.values))
    assert items[:-1] == [(0, 2), (1, 2), (2, 1)]

def test_agg_selections():
    x = np.array([0, 0, 0, 1, 1, 2, 2])
    y = np.array([1, 3, 5, 1, 7, 1, -1])
    z = np.array([0, 2, 3, 4, 5, 6, 7])
    w = np.array(['dog', 'cat', 'mouse', 'dog', 'dog', 'dog', 'cat'])

    df = vaex.from_arrays(x=x, y=y, z=z, w=w)

    df_grouped = df.groupby(df.x).agg({'count': vaex.agg.count(selection='y<=3'),
                                   'z_sum_selected': vaex.agg.sum(expression=df.z, selection='y<=3'),
                                   'z_mean_selected': vaex.agg.mean(expression=df.z, selection=df.y <= 3),
                                   'w_nuniqe_selected': vaex.agg.nunique(expression=df.w, selection=df.y <= 3, dropna=True)
                                  }).sort('x')

    assert df_grouped['count'].tolist() == [2, 1, 2]
    assert df_grouped['z_sum_selected'].tolist() == [2, 4, 13]
    assert df_grouped['z_mean_selected'].tolist() == [1, 4, 6.5]
    assert df_grouped['w_nuniqe_selected'].tolist() == [2, 1, 2]

def test_upcast():
    df = vaex.from_arrays(b=[False, True, True], i8=np.array([120, 121, 122], dtype=np.int8),
        f4=np.array([1, 1e-13, 1], dtype=np.float32))
    assert df.b.sum() == 2
    assert df.i8.sum() == 120*3 + 3
    assert df.f4.sum() == (2 + 1e-13)

    assert abs(df.b.var() - (0.2222)) < 0.01


def test_timedelta_aggretagion():
    import pandas as pd
    delta = np.array([5634, 1234, 234213, 3425, 12342], dtype='timedelta64[s]')
    x = np.array(['A', 'A', 'B', 'A', 'B'])
    df = vaex.from_arrays(delta=delta, x=x)
    pandas_df = df.to_pandas_df()

    # Wisth vaex
    groupby_df = df.groupby('x').agg({'delta_mean': vaex.agg.mean(df.delta),
                                      'delta_std': vaex.agg.std(df.delta)})

    # With pandas
    groupby_pandas_df = pandas_df.groupby('x').agg(delta_mean=('delta', pd.Series.mean),
                                                   delta_std=('delta', pd.Series.std))

    assert groupby_df.delta_mean.values.tolist() == groupby_pandas_df.delta_mean.values.astype('timedelta64[s]').tolist()
    assert groupby_df.delta_std.values.tolist() == groupby_pandas_df.delta_std.values.astype('timedelta64[s]').tolist()
