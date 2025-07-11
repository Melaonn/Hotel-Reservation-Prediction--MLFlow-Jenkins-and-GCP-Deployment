import os
import pandas as pd
from google.cloud import storage
from sklearn.model_selection import train_test_split
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *
from utils.common_functions import read_yaml

logger = get_logger(__name__)

class DataIngestion:
    def __init__(self, config):
        self.config = config["data_ingestion"]
        self.bucket_name = self.config["bucket_name"]
        self.file_name = self.config["bucket_file_name"]
        self.train_test_ratio = self.config["train_ratio"]

        os.makedirs(RAW_DIR, exist_ok=True)

        logger.info(f"Data Ingestion started with {self.bucket_name} and file is {self.file_name}")

    def log_gcp_info(self):
        try:
            logger.info("Checking available GCP buckets...")
            client = storage.Client()
            buckets = list(client.list_buckets())
            if not buckets:
                logger.warning("No buckets found!")
            for bucket in buckets:
                logger.info(f"Found bucket: {bucket.name}")

            if self.bucket_name:
                logger.info(f"Listing files in bucket '{self.bucket_name}'")
                bucket = client.get_bucket(self.bucket_name)
                blobs = list(bucket.list_blobs())
                if not blobs:
                    logger.warning(f"No files found in bucket '{self.bucket_name}'")
                for blob in blobs:
                    logger.info(f"Found file: {blob.name}")
        except Exception as e:
            logger.error(f"Error while fetching GCP bucket info: {e}")
            raise CustomException("Failed to log GCP bucket or file info", e)

    def download_csv_from_gcp(self):
        try:
            client = storage.Client()
            bucket = client.bucket(self.bucket_name)
            blob = bucket.blob(self.file_name)

            blob.download_to_filename(RAW_FILE_PATH)

            logger.info(f"CSV file is successfully downloaded to {RAW_FILE_PATH}")

        except Exception as e:
            logger.error(f"Error while downloading the csv file: {e}")
            raise CustomException("Failed to download csv file", e)

    def split_data(self):
        try:
            logger.info("Starting the splitting process")
            data = pd.read_csv(RAW_FILE_PATH)
            train_data, test_data = train_test_split(
                data, test_size=1 - self.train_test_ratio, random_state=42
            )

            train_data.to_csv(TRAIN_FILE_PATH, index=False)
            test_data.to_csv(TEST_FILE_PATH, index=False)

            logger.info(f"Train data saved to {TRAIN_FILE_PATH}")
            logger.info(f"Test data saved to {TEST_FILE_PATH}")

        except Exception as e:
            logger.error(f"Error while splitting data: {e}")
            raise CustomException("Failed to split data into training and test sets", e)

    def run(self):
        try:
            logger.info("Starting data ingestion process")
            self.log_gcp_info()                     # <<<<< Logs bucket & file info
            self.download_csv_from_gcp()
            self.split_data()
            logger.info("Data ingestion completed successfully")

        except CustomException as ce:
            logger.error(f"CustomException : {str(ce)}")

        finally:
            logger.info("Data ingestion completed")


if __name__ == "__main__":
    data_ingestion = DataIngestion(read_yaml(CONFIG_PATH))
    data_ingestion.run()
