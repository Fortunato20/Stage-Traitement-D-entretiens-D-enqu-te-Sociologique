# analyse_statistique.py
import argparse
import re
from pathlib import Path
from collections import Counter
import sys

import spacy
from stop_words import get_stop_words
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import prince

def analyser_arguments():
    analyseur = argparse.ArgumentParser(description="Analyse statistique de textes")
    
    # Argument obligatoire
    analyseur.add_argument("fichier", type=str, help="Fichier texte à analyser")
    
    # Options de filtrage
    analyseur.add_argument("--noms", action="store_true", help="Inclure les noms")
    analyseur.add_argument("--sans-noms", action="store_false", dest="noms", help="Exclure les noms")
    analyseur.add_argument("--verbes", action="store_true", help="Inclure les verbes")
    analyseur.add_argument("--sans-verbes", action="store_false", dest="verbes", help="Exclure les verbes")
    analyseur.add_argument("--adjectifs", action="store_true", help="Inclure les adjectifs")
    analyseur.add_argument("--sans-adjectifs", action="store_false", dest="adjectifs", help="Exclure les adjectifs")
    
    # Options de recherche
    analyseur.add_argument("--mots-cles", type=str, default="",
                      help="Mots-clés pour la recherche (séparés par des virgules)")
    analyseur.add_argument("--recherche-seulement", action="store_true",
                      help="Exécuter seulement la partie recherche")
    
    # Valeurs par défaut
    analyseur.set_defaults(noms=True, verbes=True, adjectifs=True)
    
    return analyseur.parse_args()

def nettoyer_texte(texte):
    texte = texte.lower()
    texte = re.sub(r"\d+", "", texte)
    ponctuation = """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
    texte = texte.translate(str.maketrans("", "", ponctuation))
    return texte.strip()

def principal():
    args = analyser_arguments()
    
    # Mode recherche seulement
    if args.recherche_seulement:
        return executer_recherche(args)
    
    # Préparation des suffixes pour les noms de fichiers
    suffixes = []
    if args.noms:
        suffixes.append("n")
    if args.verbes: 
        suffixes.append("v")
    if args.adjectifs:  
        suffixes.append("a")
    suffixe_fichier = "_".join(suffixes) if suffixes else "aucun"
    
    fichier = Path(args.fichier)
    if not fichier.is_file():
        print(f"Erreur : Le fichier {fichier} n'existe pas.")
        return 1

    # Création des dossiers de résultats
    dossier_nuages = fichier.parent / "nuages"
    dossier_afc = fichier.parent / "afc"
    dossier_nuages.mkdir(parents=True, exist_ok=True)
    dossier_afc.mkdir(parents=True, exist_ok=True)

    # Chargement des outils linguistiques
    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        print("Erreur : Le modèle linguistique 'fr_core_news_sm' n'est pas installé.")
        print("Veuillez l'installer avec : python -m spacy download fr_core_news_sm")
        return 1
        
    mots_vides = set(get_stop_words("french"))

    # Extraction des parties du texte
    parties_texte = extraire_parties(fichier)
    if not parties_texte:
        print("Erreur : Aucun texte à analyser.")
        return 1

    # --- Analyse des mots ---
    texte_complet = " ".join(partie['texte'] for partie in parties_texte)
    doc = nlp(texte_complet)
    
    # Filtrage des mots selon les critères
    mots_filtres = [
        mot.lemma_.lower()
        for mot in doc
        if mot.is_alpha
        and mot.lemma_.lower() not in mots_vides
        and (
            (args.noms and mot.pos_ == "NOUN") or
            (args.verbes and mot.pos_ == "VERB") or
            (args.adjectifs and mot.pos_ == "ADJ")
        )
    ]

    comptage_mots = Counter(mots_filtres)

    if not comptage_mots:
        print("Erreur : Aucun mot à analyser avec les critères choisis.")
    else:
        # Affichage des 20 mots les plus fréquents
        print("\nTop 20 mots les plus fréquents :")
        for mot, nb in comptage_mots.most_common(20):
            print(f"{mot} : {nb}")

        # Création du nuage de mots
        nuage = WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(comptage_mots)
        chemin_nuage = dossier_nuages / f"{fichier.stem}_wordcloud_{suffixe_fichier}.png"
        nuage.to_file(str(chemin_nuage))
        print(f"Nuage de mots sauvegardé : {chemin_nuage}")

    # --- Recherche de mots-clés ---
    mots_cles = traiter_mots_cles(args.mots_cles)
    chercher_mots_cles(parties_texte, mots_cles, nlp)

    # --- Analyse factorielle ---
    if comptage_mots:
        mots_principaux = [mot for mot, _ in comptage_mots.most_common(30)]
        donnees_afc = preparer_donnees_afc(parties_texte, mots_principaux, nlp, mots_vides, args)
        
        if donnees_afc.shape[0] >= 2 and donnees_afc.shape[1] >= 2:
            generer_graphique_afc(donnees_afc, fichier.stem, dossier_afc, suffixe_fichier)
        else:
            print("Erreur : Pas assez de données pour l'analyse factorielle.")

    print("\nAnalyse terminée avec succès !")
    print("✅ Analyse statistique terminée!")
    return 0

def executer_recherche(args):
    """Exécute seulement la recherche de mots-clés"""
    fichier = Path(args.fichier)
    if not fichier.is_file():
        print(f"Erreur : Le fichier {fichier} n'existe pas.")
        return 1

    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        print("Erreur : Le modèle linguistique 'fr_core_news_sm' n'est pas installé.")
        print("Veuillez l'installer avec : python -m spacy download fr_core_news_sm")
        return 1
        
    parties_texte = extraire_parties(fichier)
    
    if not parties_texte:
        print("Erreur : Aucun texte à analyser.")
        return 1

    mots_cles = traiter_mots_cles(args.mots_cles)
    chercher_mots_cles(parties_texte, mots_cles, nlp)
    return 0

def extraire_parties(fichier):
    """Extrait les parties du texte à analyser"""
    pattern = re.compile(r"\[(.*?)\s*-\s*(.*?)\]\s*Enquêté\s*:\s*(.*)", re.IGNORECASE)
    parties = []
    with open(fichier, 'r', encoding='utf-8') as f:
        for ligne in f:
            m = pattern.match(ligne.strip())
            if m:
                debut, fin, texte = m.groups()
                parties.append({'debut': debut, 'fin': fin, 'texte': texte})
    return parties

def traiter_mots_cles(mots_cles_input):
    """Prépare les mots-clés pour la recherche"""
    if not mots_cles_input:
        return ["nature", "environnement", "ville"]  # Mots-clés par défaut
    
    return [mot.strip().lower() 
            for mot in mots_cles_input.split(",") 
            if mot.strip()]

def chercher_mots_cles(parties_texte, mots_cles, nlp):
    """Recherche les mots-clés dans le texte"""
    print(f"\nRecherche des mots-clés : {', '.join(mots_cles)}")
    
    for mot_cle in mots_cles:
        print(f"\nMot-clé : {mot_cle}")
        trouve = False
        for partie in parties_texte:
            if mot_cle.lower() in partie['texte'].lower():
                doc_partie = nlp(partie['texte'])
                for i, mot in enumerate(doc_partie):
                    if mot.lemma_.lower() == mot_cle.lower():
                        debut = max(0, i-5)
                        fin = min(len(doc_partie), i+6)
                        contexte = " ".join(m.text for m in doc_partie[debut:fin])
                        print(f"[{partie['debut']} - {partie['fin']}] ... {contexte} ...")
                        trouve = True
        if not trouve:
            print("Aucun résultat trouvé.")

def preparer_donnees_afc(parties_texte, mots_principaux, nlp, mots_vides, args):
    """Prépare les données pour l'analyse factorielle"""
    lignes = []
    for partie in parties_texte:
        doc_partie = nlp(partie['texte'])
        mots_partie = [
            m.lemma_.lower()
            for m in doc_partie
            if m.is_alpha
            and m.lemma_.lower() not in mots_vides
            and (
                (args.noms and m.pos_ == "NOUN") or
                (args.verbes and m.pos_ == "VERB") or
                (args.adjectifs and m.pos_ == "ADJ")
            )
        ]
        compteur = Counter(mots_partie)
        lignes.append({mot: compteur.get(mot, 0) for mot in mots_principaux})

    df_afc = pd.DataFrame(lignes).fillna(0)
    # Retirer les colonnes et lignes vides
    return df_afc.loc[:, (df_afc != 0).any(axis=0)].loc[(df_afc != 0).any(axis=1)]

def generer_graphique_afc(donnees_afc, nom_base, dossier_sortie, suffixe):
    """Crée et enregistre le graphique d'analyse factorielle"""
    afc = prince.CA(n_components=2, n_iter=10, engine='scipy')
    afc = afc.fit(donnees_afc)
    coordonnees = afc.column_coordinates(donnees_afc)
    valeurs_propres = afc.eigenvalues_
    part1, part2 = round(valeurs_propres[0]*100, 2), round(valeurs_propres[1]*100, 2)

    plt.figure(figsize=(8, 6))
    plt.axhline(0, linestyle='--')
    plt.axvline(0, linestyle='--')
    plt.grid(True, linestyle=':', alpha=0.5)
    plt.scatter(coordonnees[0], coordonnees[1])
    
    for i, mot in enumerate(coordonnees.index):
        plt.text(coordonnees.iloc[i, 0], coordonnees.iloc[i, 1], mot)
    
    plt.xlabel(f"Axe 1 ({part1}%)")
    plt.ylabel(f"Axe 2 ({part2}%)")
    plt.title(f"Analyse Factorielle - {nom_base}")
    
    chemin_afc = dossier_sortie / f"{nom_base}_afc_{suffixe}.png"
    plt.tight_layout()
    plt.savefig(str(chemin_afc))
    plt.close()
    print(f"Graphique AFC sauvegardé : {chemin_afc}")

if __name__ == "__main__":
    sys.exit(principal())