FROM python:3.8-alpine
RUN apk --update add gcc build-base
RUN pip install --no-cache-dir kopf kubernetes requests
ADD verticalscaletozero-operator.py /
CMD kopf run /verticalscaletozero-operator.py