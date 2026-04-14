# Changelog

## [0.1.2] - 2026-04-15

### Ajouts

- Mise en place du changelog

### Changements

- Migration vers `hatchling`
- Retrait du support pour python `3.8` & `3.9` (fin de vie)
- Mise à jour des metadata du projet

### Corrections

- Amélioration de la detection du robot sur le port serie

## [0.1.1] - 2026-04-13

### Corrections

- Mise à jour du code copié dans le press-papier.
- Correction de la detection de version du robot.

## [0.1.0] - 2026-04-13

passage de la bibliothèque en open-source.

### Ajouts

- Mise en place de marquer individuels pour l'attende de réponse des getters
- Affiche d'une table des diagnostiques, via `print_diagnostics`
- Ajout de `get_all_candidate` et de la connexion via un protocol défini

### Changements

- Simplification du module de mise à jour
- Isolation et simplification de la couche protocol dans un sous-module
- supression de `get_diagnosics` (remplacé par `print_diagnostics`)
- suppression de `set_motor_mode` (obsolete)
- supression de trames internes (`set_manufacting_date`, `set_first_use_date`,
  `set_product_id`, `set_product_version`, ...)

### Correction

- Amélioration de la deconnection à la fin de l'execution
- Réparation des méthodes du robot:
  - `get_color_rgb_{left,center,right}`
  - `get_accessory`
- Passage vers un thread dedié pour la connexion série
- Migration vers des événements taggé pour identifier les demandes au réponses
  associées

### [0.6.4] et antérieures

*Versions de développement.*
