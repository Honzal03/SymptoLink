import joblib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator


def nacti_model_a_data():
    """Načte AI model, embeddingy a databázi (registr) z disku."""
    embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    clf = joblib.load('src_model/medical_classifier.joblib')
    metadata = joblib.load('src_model/model_metadata.joblib')
    df_registr = pd.read_csv('data/processed/czech_registre_final_small.csv')
    return embedder, clf, metadata, df_registr


def predikuj_obor(text_cz, embedder, clf, metadata, threshold=0.3):
    """Vezme text v češtině a vrátí seznam doporučených lékařských oborů."""
    try:
        text_en = GoogleTranslator(source='cs', target='en').translate(text_cz)
    except:
        text_en = text_cz

    vektor = embedder.encode([text_en])
    probs = clf.predict_proba(vektor)[0]

    above_threshold_indices = np.where(probs >= threshold)[0]

    if len(above_threshold_indices) == 0:
        return []  # Prázdný seznam indikuje, že si AI není jistá

    predicted_labels = [clf.classes_[i] for i in
                        above_threshold_indices[np.argsort(probs[above_threshold_indices])[::-1]]]

    search_specialties = []
    for label in predicted_labels:
        search_specialties.extend(metadata['clean_mapping'].get(label, []))

    return list(set(search_specialties))