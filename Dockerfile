FROM python:3.8-slim

COPY . /prmods

RUN cd /prmods && python setup.py install

ENTRYPOINT ["python", "-m", "prmods.pipeline.ods_downloader.main"]
