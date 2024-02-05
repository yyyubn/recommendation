FROM python:3.11.7-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r ins.txt
CMD ["python", "recomm.py"]