#!/bin/sh
set -e

# 1. Créer le fichier de log pour éviter les erreurs au démarrage
touch /var/log/cron.log

# 2. Exporter les variables d'environnement (essentiel pour que Python fonctionne correctement dans cron)
printenv | grep -v "no_proxy" >> /etc/environment

# 3. Écrire les tâches cron (exécution toutes les 5 minutes)
cat <<EOF > /var/spool/cron/crontabs/root
*/5 * * * * python3 /app/aria.py >> /var/log/cron.log 2>&1
*/5 * * * * python3 /app/powerstore.py >> /var/log/cron.log 2>&1
*/5 * * * * python3 /app/unity.py >> /var/log/cron.log 2>&1
*/5 * * * * python3 /app/vsphere.py >> /var/log/cron.log 2>&1
EOF

# 4. S'assurer des bonnes permissions pour le fichier crontab
chmod 600 /var/spool/cron/crontabs/root

# 5. Lancer le démon cron en arrière-plan
crond -b -L /dev/stdout

# 6. Garder le conteneur actif en affichant les logs
exec "$@"
