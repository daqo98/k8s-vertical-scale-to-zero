FROM python:3.8-alpine
RUN apk --update add gcc build-base
RUN pip install --no-cache-dir kopf kubernetes requests
ADD verticalscale_operator.py /
ADD http-scale2zero.py /
EXPOSE 80
#CMD kopf run /http-scale2zero.py
CMD ["python", "./http-scale2zero.py"]