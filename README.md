# lib-python

## Liste des évolutions souhaitées:

- Retourner des entiers en nom des string pour distance couleur à l'intérieur des list
- Mise à jour des trames de commande (commande leds, mode autonome, changement wifi)
- Envoyer un commande d'arrêt (ilo.stop() en sorti du mode game et ajouter un stop via le numéro 5)
- Limitation de l'utilisation des variable global
- Contrôle singulier d’un unique moteur
  - Idée de trame ‘im(ID)v(velocity)o’  //pb la gestion du mode servo
  - ‘im(ID)to’ exemple pour retour d’info de température
- Gérer l’accès aux capteurs I2C de la carte accessoire
  - Via une trame spécifique i9c’data’c’data’c’data’c’data’o

## Version 18:

Date de publication:
Objectif : 23/02/2024

Ajout par rapport à la version précédente:
```
• Ajout des nouvelle méthode dans list_function()
• Supprimer trait de séparation du README.md
```

## Version 17:

Date de publication:
Objectif : 23/02/2024

Ajout par rapport à la version précédente:
```
• Corriger bug photo README.md
```

## Version 16:

Date de publication:
Objectif : 22/02/2024

Ajout par rapport à la version précédente:
```
• Gestion des commentaire de paramètre de méthode
• Ajout d’un read.me
```

## Version 15:

Date de publication:
Objectif : 21/02/2024

Ajout par rapport à la version précédente:
```
• Suppression des display en paramètre
• Forcer l’installation du la lib keyboard
```

## Version 14

Date de publication:
Objectif : 21/02/2024

Ajout par rapport à la version précédente:
```
• Gestion du token pour la publication
```