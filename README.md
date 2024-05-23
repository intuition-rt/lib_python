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

## Version 28:

Date de publication:
Objectif : 16/05/2024

Ajout par rapport à la version précédente:
```
• Mise à jour des trames
```

## Version 27:

Date de publication:
Objectif : 16/05/2024

Ajout par rapport à la version précédente:
```
• Mise à jour des trames
```

## Version 26:

Date de publication:
Objectif : 16/05/2024

Ajout par rapport à la version précédente:
```
• Mise à jour de list_function
• Mise à jour des trames
• Ajout méthodes
```

## Version 25:

Date de publication:
Objectif : 15/05/2024

Ajout par rapport à la version précédente:
```
• Mise à jour de list_function
• Correction trame imu
• Correction nom méthode get_acc_motor / set_acc_motor
• Ajout drive_single_motor
```

## Version 24:

Date de publication:
Objectif : 10/05/2024

Ajout par rapport à la version précédente:
```
• Correction trame
```

## Version 23:

Date de publication:
Objectif : 10/05/2024

Ajout par rapport à la version précédente:
```
• Ajout de la trame get_imu
• Mise à jour de sa trame de retour
```

## Version 22:

Date de publication:
Objectif : 03/05/2024

Ajout par rapport à la version précédente:
```
• Ajout de la trame set_led_captor
• Modification game mode : 5 => space
```

## Version 21:

Date de publication:
Objectif : 02/05/2024

Ajout par rapport à la version précédente:
```
• Mise à jour des trames
```

## Version 20:

Date de publication:
Objectif : 02/05/2024

Ajout par rapport à la version précédente:
```
• Mise à jour des trames de retour
```

## Version 19:

Date de publication:
Objectif : 26/04/2024

Ajout par rapport à la version précédente:
```
• Mise à jour des trames de retour
```

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