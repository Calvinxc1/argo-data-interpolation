import xarray as xr


def data_qc_pass(ds: xr.Dataset, qc_vals: tuple[int, ...] = (1, 2)) -> xr.Dataset:
    qc_mask = (
        ds.PRES_QC.isin(qc_vals)
        & ds.TEMP_QC.isin(qc_vals)
        & ds.PSAL_QC.isin(qc_vals)
    )
    ds_qc = ds.where(qc_mask, drop=True)
    return ds_qc
