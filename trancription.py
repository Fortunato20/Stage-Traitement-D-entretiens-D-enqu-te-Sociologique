
import os
import sys
import whisper
from pydub import AudioSegment
from datetime import datetime

def obtenir_heure_actuelle():
    """Retourne l'heure actuelle au format HH:MM:SS"""
    return datetime.now().strftime("%H:%M:%S")

def transcrire_audio(chemin_audio, fichier_sortie):
    """
    Transcrit un fichier audio en texte avec horodatage
    Args:
        chemin_audio: Chemin vers le fichier audio à transcrire
        fichier_sortie: Fichier texte où sauvegarder la transcription
    """
    print(f"{obtenir_heure_actuelle()} - Début de la transcription")
    print(f"{obtenir_heure_actuelle()} - Utilisation du processeur (CPU)")

    # Chargement du modèle de transcription
    modele = whisper.load_model("large-v2", device="cpu")  

    # Chargement du fichier audio
    audio = AudioSegment.from_file(chemin_audio)
    duree_totale = len(audio)
    duree_segment = 5 * 60 * 1000  # Segments de 5 minutes
    nombre_segments = duree_totale // duree_segment + 1

    # Préparation du fichier de sortie
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write("")  # Crée un fichier vide

    # Traitement segment par segment
    for i in range(nombre_segments):
        debut = i * duree_segment
        fin = min((i + 1) * duree_segment, duree_totale)
        segment = audio[debut:fin]

        # Création d'un fichier temporaire pour le segment
        fichier_temporaire = os.path.join(os.path.dirname(fichier_sortie), f"segment_{i}.wav")
        segment.export(fichier_temporaire, format="wav")

        print(f"{obtenir_heure_actuelle()} - Traitement du segment {i+1}/{nombre_segments}", end=' ')

        # Transcription du segment
        resultat = modele.transcribe(
            fichier_temporaire,
            language="fr",
            task="transcribe",
            verbose=False
        )

        print("Terminé")

        # Écriture des résultats avec horodatage
        with open(fichier_sortie, 'a', encoding='utf-8') as f:
            for partie in resultat["segments"]:
                debut_sec = int(partie["start"]) + debut // 1000
                fin_sec = int(partie["end"]) + debut // 1000
                
                # Formatage de l'heure
                heure_debut = f"{debut_sec//3600:02d}:{(debut_sec%3600)//60:02d}:{debut_sec%60:02d}"
                heure_fin = f"{fin_sec//3600:02d}:{(fin_sec%3600)//60:02d}:{fin_sec%60:02d}"
                
                f.write(f"[{heure_debut} - {heure_fin}] : {partie['text'].strip()}\n")

        # Suppression du fichier temporaire
        os.remove(fichier_temporaire)

    print(f"{obtenir_heure_actuelle()} - Transcription sauvegardée : {fichier_sortie}")
    print(f"{obtenir_heure_actuelle()} - Opération réussie!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Utilisation: python transcription.py chemin/vers/audio chemin/vers/transcription.txt")
        sys.exit(1)

    chemin_audio = sys.argv[1]
    fichier_transcription = sys.argv[2]

    try:
        transcrire_audio(chemin_audio, fichier_transcription)
    except Exception as e:
        print(f"{obtenir_heure_actuelle()} - Erreur : {e}")
        sys.exit(1)