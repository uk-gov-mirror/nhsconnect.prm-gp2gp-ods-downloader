import logging

from dataclasses import asdict

from os import environ
from urllib.parse import urlparse

import boto3

from prmods.pipeline.ods_downloader.config import OdsPortalConfig

from prmods.domain.ods_portal.sources import (
    OdsDataFetcher,
    construct_organisation_metadata_from_ods_portal_response,
    PRACTICE_SEARCH_PARAMS,
    CCG_SEARCH_PARAMS,
    construct_asid_to_ods_mappings,
)
from prmods.utils.io.csv import read_gzip_csv_file
from prmods.utils.io.json import upload_json_object

logger = logging.getLogger(__name__)


def main(config):

    logging.basicConfig(level=logging.INFO)

    logger.info(config.s3_endpoint_url)
    logger.info(config.mapping_file)
    logger.info(config.output_file)

    s3 = boto3.resource("s3", endpoint_url=config.s3_endpoint_url)

    asid_lookup_object = _create_s3_object(s3, config.mapping_file)
    organisation_list_object = _create_s3_object(s3, config.output_file)

    data_fetcher = OdsDataFetcher(search_url=config.search_url)

    practice_data = data_fetcher.fetch_organisation_data(PRACTICE_SEARCH_PARAMS)
    ccg_data = data_fetcher.fetch_organisation_data(CCG_SEARCH_PARAMS)
    asid_lookup_content = read_gzip_csv_file(asid_lookup_object.get()["Body"])

    organisation_metadata = construct_organisation_metadata_from_ods_portal_response(
        practice_data,
        ccg_data,
        construct_asid_to_ods_mappings(asid_lookup_content),
    )

    upload_json_object(organisation_list_object, asdict(organisation_metadata))


def _create_s3_object(s3, url_string):
    object_url = urlparse(url_string)
    s3_bucket = object_url.netloc
    s3_key = object_url.path.lstrip("/")
    return s3.Object(s3_bucket, s3_key)


if __name__ == "__main__":
    main(config=OdsPortalConfig.from_environment_variables(environ))
