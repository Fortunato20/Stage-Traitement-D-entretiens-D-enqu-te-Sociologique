# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 11:34:24 2025

@author: User
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font
from pydub import AudioSegment
import os
import subprocess
import threading
import sys
import time
from PIL import Image, ImageTk
from pathlib import Path


class ApplicationAudio:
    def __init__(self, racine):
        self.racine = racine
        self.racine.title("Application d'Analyse Audio")
        self.racine.geometry("1000x700")
        self.racine.configure(bg="#2c3e50")
        
        # Configuration des couleurs
        self.couleur_fond = "#2c3e50"
        self.couleur_texte = "#ecf0f1"
        self.couleur_accent = "#3498db"
        self.couleur_bouton = "#2980b9"
        self.couleur_survol = "#1abc9c"
        self.couleur_journal = "#34495e"
        
        # Variables
        self.chemin_audio = tk.StringVar()
        self.debut_reference = tk.StringVar(value="0")
        self.fin_reference = tk.StringVar(value="10")
        self.chemin_transcription = tk.StringVar()
        self.chemin_diarisation = tk.StringVar()
        
        # Chemins des environnements 
        self.env_transcription = "C:/Users/Fortunato/anaconda3/envs/env_stage/python.exe"
        self.env_diarisation = "C:/Users/Fortunato/anaconda3/envs/diarisation/python.exe"
        
        # Création des pages
        self.creer_page_accueil()
        self.creer_page_traitement()
        self.creer_page_statistiques()
             
        # Barre de statut
        self.var_statut = tk.StringVar(value="Prêt")
        barre_statut = ttk.Label(self.racine, textvariable=self.var_statut, relief=tk.SUNKEN, anchor=tk.W,
                              background="#34495e", foreground="#ecf0f1")
        barre_statut.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Afficher la page d'accueil au démarrage
        self.afficher_page("accueil")
        
        # Configuration des styles
        self.configurer_styles()
        
    def actualiser_concordance(self):
        """Relancer seulement la partie concordance de l'analyse"""
        if not hasattr(self, 'analyse_terminee'):
            messagebox.showinfo("Information", "Veuillez d'abord lancer l'analyse complète")
            return
            
        mots_cles = self.var_mots_cles.get().strip()
        if not mots_cles:
            messagebox.showinfo("Information", "Veuillez entrer des mots-clés")
            return
            
        self.journal(f"Actualisation concordance avec: {mots_cles}", "stats")
        threading.Thread(target=self._executer_concordance_seulement, args=(mots_cles,)).start()
    
    def _executer_concordance_seulement(self, mots_cles):
        try:
            cmd = [
                sys.executable, 
                "analyse_statistique.py", 
                self.chemin_diarisation.get(),
                "--mots-cles", mots_cles,  # Argument en français
                "--recherche-seulement"    # Argument en français
            ]
            
            self.journal(f"Commande concordance: {' '.join(cmd)}", "stats")
            
            # Vider le journal avant nouvelle analyse
            self.journal_stats.config(state=tk.NORMAL)
            self.journal_stats.delete(1.0, tk.END)
            self.journal_stats.config(state=tk.DISABLED)
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            for line in process.stdout:
                self.journal(line.strip(), "stats")
            
            process.wait()
            
            if process.returncode == 0:
                self.journal("✅ Concordance actualisée avec succès!", "stats")
            else:
                self.journal(f"❌ Échec de l'actualisation (code: {process.returncode})", "stats")
                
        except Exception as e:
            self.journal(f"ERREUR lors de l'actualisation: {str(e)}", "stats")

    def configurer_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configuration générale
        style.configure('.', background=self.couleur_fond, foreground=self.couleur_texte, font=('Arial', 10))
        
        # Configuration des boutons
        style.configure('TButton', background=self.couleur_bouton, foreground=self.couleur_texte, 
                       borderwidth=1, font=('Arial', 10, 'bold'))
        style.map('TButton', background=[('active', self.couleur_survol), ('pressed', self.couleur_accent)])
        
        # Configuration des onglets
        style.configure('TNotebook', background=self.couleur_fond)
        style.configure('TNotebook.Tab', background="#34495e", foreground=self.couleur_texte, 
                       padding=[10, 5], font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', self.couleur_accent)])
        
        # Configuration des labels
        style.configure('TLabel', background=self.couleur_fond, foreground=self.couleur_texte)
        
        # Configuration des frames
        style.configure('TFrame', background=self.couleur_fond)

    def creer_page_accueil(self):
        self.frame_accueil = ttk.Frame(self.racine, style='TFrame')
        
        # Titre principal
        police_titre = font.Font(family='Helvetica', size=24, weight='bold')
        titre = ttk.Label(self.frame_accueil, text="Bienvenue dans l'application d'analyse audio", 
                         font=police_titre, foreground=self.couleur_accent)
        titre.pack(pady=40)
        
        # Sous-titre
        sous_titre = ttk.Label(self.frame_accueil, text="Transcription, diarisation et analyse statistique de fichiers audio", 
                             font=('Arial', 14))
        sous_titre.pack(pady=10)

        # Explications des fonctionnalités
        frame_explications = ttk.Frame(self.frame_accueil, style='TFrame')
        frame_explications.pack(pady=10, padx=50)
        ttk.Label(frame_explications, text="• Transcription : transforme votre fichier audio en texte horodaté.", wraplength=800,
                  font=('Arial', 11), foreground=self.couleur_texte).pack(anchor='w', pady=2)
        ttk.Label(frame_explications, text="• Diarisation : segmente le texte et identifie automatiquement les locuteurs.", wraplength=800,
                  font=('Arial', 11), foreground=self.couleur_texte).pack(anchor='w', pady=2)
        ttk.Label(frame_explications, text="• Analyse statistique : génère un nuage de mots, concordances et AFC.", wraplength=800,
                  font=('Arial', 11), foreground=self.couleur_texte).pack(anchor='w', pady=2)

        # Bouton pour commencer
        bouton_commencer = ttk.Button(self.frame_accueil, text="Commencer", 
                              command=lambda: self.afficher_page("traitement"),
                              style='TButton', cursor="plus")
        bouton_commencer.pack(pady=30, ipadx=20, ipady=10)
        
        # Crédits
        credits = ttk.Label(self.frame_accueil, text="© Grace Eunice Fortunato", 
                           font=('Arial', 9), foreground="#95a5a6")
        credits.pack(side=tk.BOTTOM, pady=10)

    def creer_page_traitement(self):
        self.frame_traitement = ttk.Frame(self.racine, style='TFrame')
        
        # En-tête
        frame_entete = ttk.Frame(self.frame_traitement, style='TFrame')
        frame_entete.pack(fill=tk.X, pady=(0, 20))
        
        bouton_retour = ttk.Button(frame_entete, text="← Accueil", 
                             command=lambda: self.afficher_page("accueil"))
        bouton_retour.pack(side=tk.LEFT, padx=10, pady=10)
        
        titre = ttk.Label(frame_entete, text="Traitement Audio", 
                         font=('Arial', 16, 'bold'), foreground=self.couleur_accent)
        titre.pack(side=tk.LEFT, padx=10)
        
        bouton_stats = ttk.Button(frame_entete, text="Analyse Statistique →", 
                              command=lambda: self.afficher_page("stats"))
        bouton_stats.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Contenu principal
        frame_contenu = ttk.Frame(self.frame_traitement, style='TFrame')
        frame_contenu.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Section fichier audio
        frame_audio = ttk.LabelFrame(frame_contenu, text="Fichier Audio", style='TFrame')
        frame_audio.pack(fill=tk.X, pady=10)
        
        ttk.Label(frame_audio, text="Fichier audio principal:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        entree_audio = tk.Entry(frame_audio, textvariable=self.chemin_audio, width=70,
                       bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
        entree_audio.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame_audio, text="Parcourir", command=self.charger_audio).grid(row=0, column=2, padx=5, pady=5)
        
        # Section transcription
        frame_transcription = ttk.LabelFrame(frame_contenu, text="Transcription", style='TFrame')
        frame_transcription.pack(fill=tk.X, pady=10)
        
        ttk.Button(frame_transcription, text="Lancer la transcription", command=self.executer_transcription,
                  style='TButton').pack(pady=10, padx=10, fill=tk.X)
        
        # Section référence
        frame_reference = ttk.LabelFrame(frame_contenu, text="Référence Enquêtrice", style='TFrame')
        frame_reference.pack(fill=tk.X, pady=10)
        
        ttk.Label(frame_reference, text="Extraire référence (secondes):").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        tk.Entry(frame_reference, textvariable=self.debut_reference, width=10,
         bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1").grid(row=0, column=1, sticky='w', padx=5)
        ttk.Label(frame_reference, text="à").grid(row=0, column=2, padx=5)
        tk.Entry(frame_reference, textvariable=self.fin_reference, width=10,
         bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1").grid(row=0, column=3, sticky='e', padx=5)
        ttk.Button(frame_reference, text="Extraire", command=self.extraire_reference).grid(row=0, column=4, padx=5)
        
        # Section diarisation
        frame_diarisation = ttk.LabelFrame(frame_contenu, text="Diarisation", style='TFrame')
        frame_diarisation.pack(fill=tk.X, pady=10)
        
        ttk.Button(frame_diarisation, text="Lancer la diarisation", command=self.executer_diarisation,
                  style='TButton').pack(pady=10, padx=10, fill=tk.X)
        
        # Journal d'exécution
        frame_journal = ttk.LabelFrame(frame_contenu, text="Journal d'exécution", style='TFrame')
        frame_journal.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.journal_texte = scrolledtext.ScrolledText(frame_journal, height=10, bg=self.couleur_journal, fg=self.couleur_texte,
                                                insertbackground=self.couleur_texte)
        self.journal_texte.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.journal_texte.config(state=tk.DISABLED, font=('Consolas', 9))

    def creer_page_statistiques(self):
        self.frame_stats = ttk.Frame(self.racine, style='TFrame')
        
        # En-tête
        frame_entete = ttk.Frame(self.frame_stats, style='TFrame')
        frame_entete.pack(fill=tk.X, pady=(0, 20))
        
        bouton_retour = ttk.Button(frame_entete, text="← Traitement Audio", 
                             command=lambda: self.afficher_page("traitement"))
        bouton_retour.pack(side=tk.LEFT, padx=10, pady=10)
        
        titre = ttk.Label(frame_entete, text="Analyse Statistique", 
                         font=('Arial', 16, 'bold'), foreground=self.couleur_accent)
        titre.pack(side=tk.LEFT, padx=10)
        
        # Contenu principal
        frame_contenu = ttk.Frame(self.frame_stats, style='TFrame')
        frame_contenu.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Cadre pour les options
        self.frame_controles_stats = ttk.LabelFrame(frame_contenu, text="Types de mots à inclure")
        self.frame_controles_stats.pack(fill=tk.X, pady=(0, 10))
        
        # Cases à cocher
        self.inclure_noms = tk.BooleanVar(value=True)
        self.inclure_verbes = tk.BooleanVar(value=True)
        self.inclure_adjectifs = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(self.frame_controles_stats, text="Noms", variable=self.inclure_noms).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(self.frame_controles_stats, text="Verbes", variable=self.inclure_verbes).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(self.frame_controles_stats, text="Adjectifs", variable=self.inclure_adjectifs).pack(side=tk.LEFT, padx=10)
        
        # Cadre pour les mots-clés
        frame_concordance = ttk.LabelFrame(frame_contenu, text="Concordance personnalisée")
        frame_concordance.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame_concordance, text="Mots-clés (séparés par des virgules):").pack(side=tk.LEFT, padx=(10, 5))
        
        self.var_mots_cles = tk.StringVar(value="nature, environnement, ville")
        entree_mots_cles = tk.Entry(frame_concordance, textvariable=self.var_mots_cles, width=50,
                                bg="#34495e", fg="#ecf0f1", insertbackground="#ecf0f1")
        entree_mots_cles.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        ttk.Button(frame_concordance, text="Actualiser concordances", 
                  command=self.actualiser_concordance).pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Section statistiques
        frame_resultats = ttk.LabelFrame(frame_contenu, text="Résultats statistiques")
        frame_resultats.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Frame container pour les résultats
        self.frame_resultats_stats = ttk.Frame(frame_resultats, style='TFrame')
        self.frame_resultats_stats.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Texte temporaire
        self.texte_placeholder = ttk.Label(self.frame_resultats_stats,
                                         text="Les résultats statistiques s'afficheront ici après l'analyse",
                                         font=('Arial', 12), foreground="#95a5a6")
        self.texte_placeholder.pack(expand=True, pady=50)
        
        # Bouton pour lancer l'analyse
        ttk.Button(frame_resultats, text="Lancer l'analyse statistique", command=self.executer_statistiques,
                  style='TButton').pack(pady=20, padx=10, fill=tk.X)
        
        # Journal d'exécution
        frame_journal = ttk.LabelFrame(frame_contenu, text="Journal d'exécution", style='TFrame')
        frame_journal.pack(fill=tk.BOTH, pady=10)
        
        self.journal_stats = scrolledtext.ScrolledText(frame_journal, height=10, bg=self.couleur_journal, fg=self.couleur_texte,
                                                      insertbackground=self.couleur_texte)
        self.journal_stats.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.journal_stats.config(state=tk.DISABLED, font=('Consolas', 9))
            

    def afficher_page(self, nom_page):
        # Cacher toutes les pages
        self.frame_accueil.pack_forget()
        self.frame_traitement.pack_forget()
        self.frame_stats.pack_forget()
        
        # Afficher la page demandée
        if nom_page == "accueil":
            self.frame_accueil.pack(fill=tk.BOTH, expand=True)
        elif nom_page == "traitement":
            self.frame_traitement.pack(fill=tk.BOTH, expand=True)
        elif nom_page == "stats":
            self.frame_stats.pack(fill=tk.BOTH, expand=True)
        
        # Mettre à jour la barre de statut
        self.var_statut.set(f"Page affichée: {nom_page.capitalize()}")

    def journal(self, message, page="traitement"):
        """Journalisation avec coloration syntaxique"""
        widget_journal = self.journal_texte if page == "traitement" else self.journal_stats
        
        widget_journal.config(state=tk.NORMAL)
        
        # Appliquer une coloration en fonction du type de message
        if "✅" in message or "succès" in message.lower():
            tag = "success"
        elif "❌" in message or "erreur" in message.lower():
            tag = "error"
        elif "démarrage" in message.lower() or "commande" in message.lower():
            tag = "info"
        else:
            tag = "normal"
        
        widget_journal.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n", tag)
        widget_journal.see(tk.END)
        widget_journal.config(state=tk.DISABLED)
        
        # Mettre à jour la barre de statut avec le dernier message
        self.var_statut.set(message)
        
        # Forcer la mise à jour de l'interface
        self.racine.update_idletasks()

    def charger_audio(self):
        chemin_fichier = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3 *.wav *.m4a")])
        if chemin_fichier:
            self.chemin_audio.set(chemin_fichier)
            base = os.path.splitext(chemin_fichier)[0]
            self.chemin_transcription.set(base + "_transcript.txt")
            self.chemin_diarisation.set(base + "_diarization.txt")
            self.journal(f"Fichier audio sélectionné: {chemin_fichier}")
            

    def executer_transcription(self):
        if not self.chemin_audio.get():
            messagebox.showerror("Erreur", "Sélectionnez d'abord un fichier audio")
            return
        self.journal("Démarrage de la transcription...")
        threading.Thread(target=self._executer_transcription).start()

    def _executer_transcription(self):
        try:
            cmd = [
                self.env_transcription,
                "trancription.py",
                self.chemin_audio.get(),
                self.chemin_transcription.get()
            ]
            self.journal("Commande: " + " ".join(cmd))
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            for line in process.stdout:
                self.journal(line.strip())
            process.wait()

            if process.returncode == 0:
                self.journal("✅ Transcription réussie!")
                messagebox.showinfo("Succès", "Transcription terminée avec succès!")
            else:
                self.journal(f"❌ Échec de la transcription (code: {process.returncode})")
                messagebox.showerror("Erreur", f"Échec de la transcription (code: {process.returncode})")

        except Exception as e:
            self.journal(f"ERREUR: {str(e)}")
            messagebox.showerror("Erreur", str(e))

    def extraire_reference(self):
        try:
            debut = float(self.debut_reference.get()) * 1000
            fin = float(self.fin_reference.get()) * 1000
            if not self.chemin_audio.get():
                messagebox.showerror("Erreur", "Sélectionnez d'abord un fichier audio")
                return
            audio = AudioSegment.from_file(self.chemin_audio.get())
            if fin > len(audio):
                messagebox.showerror("Erreur", "La fin spécifiée dépasse la durée de l'audio")
                return
            reference_audio = audio[debut:fin]
            chemin_ref = os.path.splitext(self.chemin_audio.get())[0] + "_REF.wav"
            reference_audio.export(chemin_ref, format="wav")
            self.journal(f"Référence extraite: {chemin_ref}")
            messagebox.showinfo("Succès", f"Référence extraite: {chemin_ref}")
        except Exception as e:
            self.journal(f"ERREUR extraction: {str(e)}")
            messagebox.showerror("Erreur", str(e))

    def executer_diarisation(self):
        if not all([self.chemin_audio.get(), self.chemin_transcription.get()]):
            messagebox.showerror("Erreur", "Complétez la transcription d'abord")
            return

        chemin_ref = os.path.splitext(self.chemin_audio.get())[0] + "_REF.wav"
        if not os.path.exists(chemin_ref):
            messagebox.showerror("Erreur", "Extrayez d'abord la référence")
            return

        self.journal("Démarrage de la diarisation...")
        threading.Thread(target=self._executer_diarisation, args=(chemin_ref,)).start()

    def _executer_diarisation(self, chemin_ref):
        try:
            cmd = [
                self.env_diarisation,
                "diarisation.py",
                self.chemin_audio.get(),
                chemin_ref,
                self.chemin_transcription.get(),
                self.chemin_diarisation.get()
            ]
            self.journal("Commande: " + " ".join(cmd))
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            for line in process.stdout:
                self.journal(line.strip())
            process.wait()

            if process.returncode == 0:
                self.journal("✅ Diarisation réussie!")
                messagebox.showinfo("Succès", "Diarisation terminée avec succès!")
                # Aller automatiquement à la page des statistiques
                self.racine.after(1000, lambda: self.afficher_page("stats"))
            else:
                self.journal(f"❌ Échec de la diarisation (code: {process.returncode})")
                messagebox.showerror("Erreur", f"Échec de la diarisation (code: {process.returncode})")

        except Exception as e:
            self.journal(f"ERREUR: {str(e)}")
            messagebox.showerror("Erreur", str(e))

    def executer_statistiques(self):
        if not self.chemin_diarisation.get():
            messagebox.showerror("Erreur", "Le fichier de transcription diarisé est manquant")
            return
        self.journal("Démarrage de l'analyse statistique...", "stats")
        threading.Thread(target=self._executer_statistiques).start()

    def _executer_statistiques(self):
        try:
            # 1) Commande avec flags sélectionnés
            cmd = [sys.executable, "analyse_statistique.py", self.chemin_diarisation.get()]
        
            # Options de filtrage (en français maintenant)
            cmd.append("--noms" if self.inclure_noms.get() else "--sans-noms")
            cmd.append("--verbes" if self.inclure_verbes.get() else "--sans-verbes")
            cmd.append("--adjectifs" if self.inclure_adjectifs.get() else "--sans-adjectifs")
            
            # Mots-clés de concordance
            mots_cles = self.var_mots_cles.get().strip()
            if mots_cles:
                cmd.extend(["--mots-cles", mots_cles])
            
            self.journal(f"[DEBUG] noms={self.inclure_noms.get()}, verbes={self.inclure_verbes.get()}, adjectifs={self.inclure_adjectifs.get()}", "stats")
            self.journal("Commande: " + " ".join(cmd), "stats")
        
            # 2) Exécution
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                self.journal(line.strip(), "stats")
            process.wait()
        
            # 3) Affichage si succès
            if process.returncode == 0:
                self.analyse_terminee = True  # Marquer que l'analyse est terminée
                self.journal("✅ Analyse statistique terminée!", "stats")
                messagebox.showinfo("Succès", "Analyse statistique réalisée avec succès!")
        
                # Vider l'ancien contenu
                for w in self.frame_resultats_stats.winfo_children():
                    w.destroy()
        
                # Créer suffixe d'options
                opts = []
                if self.inclure_noms.get(): opts.append("n")
                if self.inclure_verbes.get(): opts.append("v")
                if self.inclure_adjectifs.get(): opts.append("a")
                suf = "_".join(opts) if opts else "none"
        
                base = Path(self.chemin_diarisation.get()).with_suffix('')
                d = base.parent
        
                chemin_nuage = d / "nuages" / f"{base.name}_wordcloud_{suf}.png"
                chemin_afc = d / "afc" / f"{base.name}_afc_{suf}.png"
        
                # Afficher nuage
                try:
                    img_nuage = Image.open(chemin_nuage).resize((400, 250), Image.LANCZOS)
                    photo_nuage = ImageTk.PhotoImage(img_nuage)
                    label_nuage = ttk.Label(self.frame_resultats_stats, image=photo_nuage)
                    label_nuage.image = photo_nuage
                    label_nuage.pack(side=tk.LEFT, expand=True, padx=10, pady=10)
                except Exception as e:
                    self.journal(f"⚠️ Impossible d'afficher le nuage de mots: {e}", "stats")
        
                # Afficher AFC
                try:
                    img_afc = Image.open(chemin_afc).resize((400, 250), Image.LANCZOS)
                    photo_afc = ImageTk.PhotoImage(img_afc)
                    label_afc = ttk.Label(self.frame_resultats_stats, image=photo_afc)
                    label_afc.image = photo_afc
                    label_afc.pack(side=tk.RIGHT, expand=True, padx=10, pady=10)
                except Exception as e:
                    self.journal(f"⚠️ Impossible d'afficher l'AFC: {e}", "stats")
        
            else:
                self.journal(f"❌ Échec de l'analyse (code: {process.returncode})", "stats")
                messagebox.showerror("Erreur", f"Code retour: {process.returncode}")
        
        except Exception as e:
            self.journal(f"ERREUR analyse: {e}", "stats")
            messagebox.showerror("Erreur", str(e))
    

if __name__ == "__main__":
    racine = tk.Tk()
    app = ApplicationAudio(racine)
    
    # Configuration des tags de couleur pour le journal
    app.journal_texte.tag_config("success", foreground="#2ecc71")
    app.journal_texte.tag_config("error", foreground="#e74c3c")
    app.journal_texte.tag_config("info", foreground="#3498db")
    app.journal_texte.tag_config("normal", foreground="#ecf0f1")
    
    app.journal_stats.tag_config("success", foreground="#2ecc71")
    app.journal_stats.tag_config("error", foreground="#e74c3c")
    app.journal_stats.tag_config("info", foreground="#3498db")
    app.journal_stats.tag_config("normal", foreground="#ecf0f1")
    
    racine.mainloop()