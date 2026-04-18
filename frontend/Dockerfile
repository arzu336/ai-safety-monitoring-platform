FROM python:3.12-slim

WORKDIR /app

COPY requirements-frontend.txt /app/requirements-frontend.txt

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements-frontend.txt

COPY . /app

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]