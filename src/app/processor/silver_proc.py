"""Silver processor module."""

import logging
from pathlib import Path
import datetime
import polars as pl

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

pl.Config.set_tbl_rows(1000)
pl.Config.set_tbl_cols(1000)
pl.Config.set_fmt_str_lengths(1000)
pl.Config.set_tbl_width_chars(1000)


def get_project_root() -> Path:
    """Get project root path."""
    return Path(__file__).resolve().parent.parent.parent


# join_key_date = pl.date(2025, 1, 27)
join_key_monday_date = datetime.date.today() - datetime.timedelta(
    days=datetime.date.today().weekday()
)
logging.info(join_key_monday_date)

WRITE_SILVER = True

delta_write_options = {"partition_by": "monday_of_week"}

if WRITE_SILVER:
    # BRONZE has a flatten schema now
    # Prepare refined data model on SILVER
    source_path = f"{get_project_root()}/lakehouse/bronze/media_tv"
    dest_path = f"{get_project_root()}/lakehouse/silver/media_tv"

    (
        pl.read_delta(source_path)
        .filter(pl.col("monday_of_week") == join_key_monday_date)
        .rename({"payload.cost": "cost_tv"})
        .rename({"payload.brand": "brand"})
        .rename({"payload.sub_brand": "sub_brand"})
        .rename({"payload.campaign_name": "campaign_name"})
        .with_columns(cost_tv=pl.col("cost_tv").cast(pl.Float32))
    ).write_delta(
        target=dest_path, mode="overwrite", delta_write_options=delta_write_options
    )

    source_path = f"{get_project_root()}/lakehouse/bronze/media_radio"
    dest_path = f"{get_project_root()}/lakehouse/silver/media_radio"

    (
        pl.read_delta(f"{get_project_root()}/lakehouse/bronze/media_radio")
        .filter(pl.col("monday_of_week") == join_key_monday_date)
        .rename({"payload.cost": "cost_radio"})
        .rename({"payload.brand": "brand"})
        .rename({"payload.sub_brand": "sub_brand"})
        .rename({"payload.campaign_name": "campaign_name"})
        .with_columns(cost_radio=pl.col("cost_radio").cast(pl.Float32))
    ).write_delta(
        target=dest_path, mode="overwrite", delta_write_options=delta_write_options
    )

    source_path = f"{get_project_root()}/lakehouse/bronze/sale"
    dest_path = f"{get_project_root()}/lakehouse/silver/sale"

    (
        pl.read_delta(source_path)
        .filter(pl.col("monday_of_week") == join_key_monday_date)
        .rename({"payload.sale_amount": "sale_amount"})
        .rename({"payload.brand": "brand"})
        .rename({"payload.sub_brand": "sub_brand"})
        .rename({"payload.campaign_name": "campaign_name"})
        .rename({"payload.mmm_model": "mmm_model"})
        .with_columns(sale_amount=pl.col("sale_amount").cast(pl.Float32))
    ).write_delta(
        target=dest_path, mode="overwrite", delta_write_options=delta_write_options
    )
else:
    logger.info("Skipping silver write.")

# Read SILVER and aggregate to GOLD
silver_media_radio = pl.read_delta(
    f"{get_project_root()}/lakehouse/silver/media_radio"
).filter(pl.col("monday_of_week") == join_key_monday_date)

silver_media_tv = pl.read_delta(
    f"{get_project_root()}/lakehouse/silver/media_tv"
).filter(pl.col("monday_of_week") == join_key_monday_date)

silver_sale = pl.read_delta(f"{get_project_root()}/lakehouse/silver/sale").filter(
    pl.col("monday_of_week") == join_key_monday_date
)

agg_silver_media_radio = (
    silver_media_radio.with_columns(sum_cost_radio=pl.sum("cost_radio"))
    .select(
        "monday_of_week",
        "brand",
        "sub_brand",
        "campaign_name",
        "channel",
        "sum_cost_radio",
    )
    .unique()
)
logger.info(agg_silver_media_radio)

agg_silver_media_tv = (
    silver_media_tv.with_columns(sum_cost_tv=pl.sum("cost_tv"))
    .select(
        "monday_of_week",
        "brand",
        "sub_brand",
        "campaign_name",
        "channel",
        "sum_cost_tv",
    )
    .unique()
)
logger.info(agg_silver_media_tv)

agg_silver_sale = (
    silver_sale.with_columns(sum_sale_amount=pl.sum("sale_amount"))
    .select(
        "monday_of_week",
        "brand",
        "sub_brand",
        "campaign_name",
        "channel",
        "sum_sale_amount",
        "mmm_model",
    )
    .unique()
)
logger.info(agg_silver_sale)

joined_media_sale = agg_silver_media_radio.join(
    agg_silver_media_tv, on=["monday_of_week", "brand"]
).join(agg_silver_sale, on=["monday_of_week", "brand"])

# Write GOLD
dest_path = f"{get_project_root()}/lakehouse/gold/report_model"
(
    joined_media_sale.select(
        "monday_of_week",
        "brand",
        "sub_brand",
        "campaign_name",
        "channel",
        "sum_cost_radio",
        "sum_cost_tv",
        "sum_sale_amount",
        "mmm_model",
    ).write_delta(
        target=dest_path, mode="overwrite", delta_write_options=delta_write_options
    )
)

logger.info(
    pl.read_delta(f"{get_project_root()}/lakehouse/gold/report_model").filter(
        pl.col("monday_of_week") == join_key_monday_date
    )
)
