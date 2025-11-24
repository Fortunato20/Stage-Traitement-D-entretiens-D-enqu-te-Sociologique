from pyannote.audio import Pipeline, Inference, Audio
import torch
import numpy as np
import re, os, sys
from scipy.spatial.distance import cdist
from pydub import AudioSegment
import time

# Configuration
TOKEN_HUGGINGFACE = "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"
MAX_TENTATIVES = 3
DELAI_RETENTATIVE = 10

def convertir_en_wav(chemin_audio):
    """Convertit un fichier audio en format WAV si nécessaire"""
    if chemin_audio.lower().endswith('.wav'):
        return chemin_audio
    chemin_sortie = os.path.splitext(chemin_audio)[0] + '.wav'
    audio = AudioSegment.from_file(chemin_audio)
    audio.export(chemin_sortie, format="wav")
    return chemin_sortie

def convertir_temps_en_secondes(temps_str):
    """Convertit un temps format hh:mm:ss en secondes"""
    if not isinstance(temps_str, str) or temps_str.count(":") != 2:
        raise ValueError(f"Format de temps incorrect : '{temps_str}'")
    heures, minutes, secondes = map(int, temps_str.split(":"))
    return heures * 3600 + minutes * 60 + secondes

def convertir_secondes_en_temps(secondes):
    """Convertit des secondes en format hh:mm:ss"""
    return f"{secondes//3600:02d}:{(secondes%3600)//60:02d}:{secondes%60:02d}"

def executer_diarisation(principal_audio, reference_audio, fichier_transcription, fichier_sortie):
    """Exécute le processus complet de diarisation"""
    try:
        # Vérification des fichiers d'entrée
        for chemin in [principal_audio, reference_audio, fichier_transcription]:
            if not os.path.exists(chemin):
                print(f"Erreur: Fichier introuvable : {chemin}")
                return False

        # Conversion des fichiers audio en WAV
        reference_wav = convertir_en_wav(reference_audio)
        principal_wav = convertir_en_wav(principal_audio)

        # Obtenir la durée du fichier audio principal
        audio = AudioSegment.from_file(principal_wav)
        duree_secondes = audio.duration_seconds

        # Chargement du modèle de diarisation
        modele_diarisation = None
        for tentative in range(MAX_TENTATIVES):
            try:
                modele_diarisation = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=TOKEN_HUGGINGFACE
                )
                break
            except Exception as e:
                print(f"Échec du chargement (tentative {tentative+1}): {e}")
                time.sleep(DELAI_RETENTATIVE)
        
        if modele_diarisation is None:
            print("Échec du chargement du modèle de diarisation")
            return False

        print("Début de la diarisation...")
        resultat_diarisation = None
        for tentative in range(MAX_TENTATIVES):
            try:
                resultat_diarisation = modele_diarisation(principal_wav)
                break
            except Exception as e:
                print(f"Erreur lors de la diarisation (tentative {tentative+1}): {e}")
                time.sleep(DELAI_RETENTATIVE)
        
        if resultat_diarisation is None:
            print("Échec de la diarisation")
            return False
        
        print(f"Diarisation réussie - segments trouvés: {len(resultat_diarisation)}")

        # Extraction des caractéristiques vocales
        modele_caracteristiques = Inference("pyannote/embedding", use_auth_token=TOKEN_HUGGINGFACE)
        caracteristiques_reference = modele_caracteristiques(reference_wav).data.mean(axis=0)

        caracteristiques = {}
        chargeur_audio = Audio(sample_rate=16000, mono=True)
        
        for segment, _, locuteur in resultat_diarisation.itertracks(yield_label=True):
            if segment.end > duree_secondes:
                continue
            onde, taux_echantillonage = chargeur_audio.crop(principal_wav, segment)
            carac = modele_caracteristiques({'waveform': onde, 'sample_rate': taux_echantillonage}).data.mean(axis=0)
            caracteristiques.setdefault(locuteur, []).append(carac)

        if not caracteristiques:
            print("Aucun segment valide pour l'analyse")
            return False

        # Identification de l'enquêtrice
        distances = {
            locuteur: cdist([np.mean(liste, axis=0)], [caracteristiques_reference], 'cosine')[0][0]
            for locuteur, liste in caracteristiques.items()
        }
        enqueteuse = min(distances, key=distances.get)
        print(f"Enquêtrice identifiée : {enqueteuse}")

        # Lecture du fichier de transcription
        with open(fichier_transcription, 'r', encoding='utf-8') as f:
            segments_texte = [ligne.strip() for ligne in f if ligne.strip()]

        resultats = []
        dernier_locuteur = enqueteuse
        
        # Expression régulière pour analyser les segments de texte
        pattern = re.compile(r"\[?\s*(\d{2}:\d{2}:\d{2})\s*[-:]\s*(\d{2}:\d{2}:\d{2})\s*\]?\s*[:\-]?\s*(.+)")
        
        for segment in segments_texte:
            match = pattern.match(segment)
            if not match:
                print(f"Segment ignoré (format incorrect) : {segment}")
                continue
            
            debut_str, fin_str, texte = match.groups()
            
            try:
                debut_sec = convertir_temps_en_secondes(debut_str)
                fin_sec = convertir_temps_en_secondes(fin_str)
            except ValueError as e:
                print(f"Segment ignoré (temps incorrect) : {e}")
                continue

            duree_par_locuteur = {}
            for segment_audio, _, locuteur in resultat_diarisation.itertracks(yield_label=True):
                if segment_audio.end > duree_secondes:
                    continue
                if segment_audio.end < debut_sec or segment_audio.start > fin_sec:
                    continue
                chevauchement = min(segment_audio.end, fin_sec) - max(segment_audio.start, debut_sec)
                if chevauchement > 0:
                    duree_par_locuteur[locuteur] = duree_par_locuteur.get(locuteur, 0) + chevauchement
            
            locuteur_actif = max(duree_par_locuteur, key=duree_par_locuteur.get) if duree_par_locuteur else dernier_locuteur
            dernier_locuteur = locuteur_actif
            role = "Enquêtrice" if locuteur_actif == enqueteuse else "Enquêté"
            resultats.append(f"[{convertir_secondes_en_temps(debut_sec)} - {convertir_secondes_en_temps(fin_sec)}] {role} : {texte}")

        # Écriture des résultats
        with open(fichier_sortie, 'w', encoding='utf-8') as f:
            f.write("\n".join(resultats))
        
        print("Résultats enregistrés dans :", fichier_sortie)
        return True

    except Exception as e:
        print("Erreur lors de la diarisation :", e)
        return False

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Utilisation: python diarisation.py audio_principal audio_reference transcription.txt resultat.txt")
        sys.exit(1)
    
    succes = executer_diarisation(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    sys.exit(0 if succes else 1)