import streamlit as st
import os
import pandas as pd
from datetime import datetime
from detector import detect_ppe
from rules import evaluate_safety

st.set_page_config(
    page_title="AI Construction Safety Monitor",
    page_icon="🏗️",
    layout="wide"
)

LOG_FILE = "violation_log.csv"

def get_status_badge(risk_level):
    if risk_level == "Düşük":
        return "🟢 Güvenli"
    elif risk_level == "Orta":
        return "🟡 Dikkat"
    elif risk_level == "Yüksek":
        return "🔴 Kritik"
    return "⚪ Bilinmiyor"

def get_recommendations(safety_result):
    recommendations = []

    if safety_result["no_helmet"] > 0:
        recommendations.append("Baret kullanmayan çalışanlar için sahada anlık KKE kontrolü yapılmalı.")

    if safety_result["no_vest"] > 0:
        recommendations.append("Reflektif yelek kullanımı denetlenmeli ve eksikler giderilmeli.")

    if safety_result["risk"] == "Yüksek":
        recommendations.append("Saha sorumlusu tarafından ilgili bölgede acil güvenlik denetimi başlatılmalı.")
        recommendations.append("İhlal tespit edilen alan geçici olarak kontrol altına alınmalı.")

    if safety_result["risk"] == "Orta":
        recommendations.append("Vardiya öncesi kısa güvenlik bilgilendirmesi yapılmalı.")

    if safety_result["risk"] == "Düşük":
        recommendations.append("Mevcut saha düzeni korunmalı ve periyodik izleme sürdürülmeli.")

    return recommendations

def build_summary_record(file_name, detection_result, safety_result):
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_name": file_name,
        "person_count": detection_result["person"],
        "helmet_count": detection_result["helmet"],
        "vest_count": detection_result["vest"],
        "no_helmet_count": safety_result["no_helmet"],
        "no_vest_count": safety_result["no_vest"],
        "risk_level": safety_result["risk"]
    }

def append_to_log(record, log_file=LOG_FILE):
    df_new = pd.DataFrame([record])

    if os.path.exists(log_file):
        df_old = pd.read_csv(log_file)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(log_file, index=False)
    return df_all

def load_log(log_file=LOG_FILE):
    if os.path.exists(log_file):
        return pd.read_csv(log_file)
    return pd.DataFrame(columns=[
        "timestamp",
        "file_name",
        "person_count",
        "helmet_count",
        "vest_count",
        "no_helmet_count",
        "no_vest_count",
        "risk_level"
    ])

st.title("🏗️ AI Construction Safety Monitor")
st.caption("Şantiye güvenliği için yapay zeka destekli PPE izleme paneli")

st.markdown("---")

uploaded_file = st.file_uploader(
    "Bir şantiye görseli yükleyin",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    os.makedirs("sample_data", exist_ok=True)
    image_path = os.path.join("sample_data", uploaded_file.name)

    with open(image_path, "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Görsel analiz ediliyor..."):
        detection_result = detect_ppe(image_path)
        safety_result = evaluate_safety(detection_result)

    status_badge = get_status_badge(safety_result["risk"])
    recommendations = get_recommendations(safety_result)

    summary_record = build_summary_record(
        uploaded_file.name,
        detection_result,
        safety_result
    )

    # Aynı analiz tekrar tekrar log'a eklenmesin diye butonla kaydet
    if "last_record" not in st.session_state:
        st.session_state.last_record = None

    st.subheader("Genel Durum")
    st.info(f"Durum: {status_badge} | Risk Seviyesi: {safety_result['risk']}")

    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        st.subheader("Yüklenen Görsel")
        st.image(image_path, caption="Orijinal Görsel", use_container_width=True)

        st.subheader("Model Çıktısı")
        st.image(
            detection_result["output_image"],
            caption="Tespit Sonucu",
            use_container_width=True
        )

    with col_right:
        st.subheader("Analiz Özeti")

        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            st.metric("Çalışan Sayısı", detection_result["person"])
            st.metric("Baret Sayısı", detection_result["helmet"])
            st.metric("Yelek Sayısı", detection_result["vest"])

        with metric_col2:
            st.metric("Baretsiz Çalışan", safety_result["no_helmet"])
            st.metric("Yeleksiz Çalışan", safety_result["no_vest"])
            st.metric("Risk Seviyesi", safety_result["risk"])

        st.subheader("Uyarılar")
        for alert in safety_result["alerts"]:
            st.warning(alert)

        st.subheader("Önerilen Aksiyonlar")
        for rec in recommendations:
            st.write(f"- {rec}")

    st.markdown("---")

    st.subheader("Tespit Detayları")

    if detection_result["boxes"]:
        df_boxes = pd.DataFrame(detection_result["boxes"])
        df_boxes["conf"] = df_boxes["conf"].round(3)

        st.dataframe(
            df_boxes[["class", "conf", "x1", "y1", "x2", "y2"]],
            use_container_width=True
        )
    else:
        st.info("Herhangi bir nesne tespit edilmedi.")

    st.markdown("---")

    st.subheader("Analiz Kaydı ve Rapor")

    summary_df = pd.DataFrame([summary_record])
    st.dataframe(summary_df, use_container_width=True)

    csv_bytes = summary_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Bu Analizi CSV Olarak İndir",
        data=csv_bytes,
        file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    if st.button("Analizi İhlal Geçmişine Kaydet"):
        all_logs = append_to_log(summary_record)
        st.session_state.last_record = summary_record
        st.success("Analiz kaydı violation_log.csv dosyasına eklendi.")

    st.success("Analiz tamamlandı.")

else:
    st.info("Başlamak için bir şantiye görseli yükleyin.")

    st.subheader("Bu uygulama ne yapar?")
    st.write("""
    Bu sistem, yüklenen şantiye görselleri üzerinde:
    - çalışan tespiti yapar,
    - baret ve yelek kullanımını analiz eder,
    - eksik KKE durumlarını belirler,
    - risk seviyesini hesaplar,
    - güvenlik aksiyonları önerir,
    - analiz sonuçlarını CSV raporu olarak indirmenizi sağlar.
    """)

st.markdown("---")
st.subheader("İhlal Geçmişi")

log_df = load_log()

if not log_df.empty:
    st.dataframe(log_df, use_container_width=True)

    log_csv = log_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Tüm İhlal Geçmişini CSV Olarak İndir",
        data=log_csv,
        file_name="violation_log.csv",
        mime="text/csv"
    )
else:
    st.info("Henüz kayıtlı ihlal geçmişi bulunmuyor.")