# OCRBox Deployment Checklist

Use this checklist to ensure proper deployment of OCRBox.

## Pre-Deployment

### Requirements
- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 2.0+)
- [ ] Google Gemini API key obtained
- [ ] (Optional) Dropbox App created and configured
- [ ] (Optional) Telegram bot created

### Configuration
- [ ] `.env` file created from `.env.example`
- [ ] `GEMINI_API_KEY` set in `.env`
- [ ] `MODE` set to `local` or `dropbox`
- [ ] (If Dropbox) `DROPBOX_APP_KEY` and `DROPBOX_APP_SECRET` set
- [ ] (If Dropbox) `ALLOWED_ACCOUNTS` configured
- [ ] (If notifications) Telegram/Email credentials configured

### Infrastructure
- [ ] Data directories created (`data/tokens`, `data/output`, `data/archive`, `data/watch`)
- [ ] Permissions set correctly (`chmod 700 data/tokens`)
- [ ] Port 8080 available (or changed in `.env`)

## Deployment

### Build & Start
- [ ] Run `docker-compose build`
- [ ] Run `docker-compose up -d`
- [ ] Check logs: `docker-compose logs -f`
- [ ] Verify no errors in startup

### Local Mode Testing
- [ ] Add test image to `data/watch/`
- [ ] Verify image is processed
- [ ] Check output in `data/output/`
- [ ] Verify image moved to `data/archive/`
- [ ] Check notification received (if enabled)

### Dropbox Mode Testing
- [ ] Visit `http://localhost:8080`
- [ ] Complete OAuth authorization
- [ ] Verify account authorized in logs
- [ ] Upload test image to Dropbox App Folder
- [ ] Wait for poll interval (default 30s)
- [ ] Verify image processed
- [ ] Check output in `data/output/`

## Post-Deployment

### Monitoring
- [ ] Configure log rotation if needed
- [ ] Set up monitoring/alerting (optional)
- [ ] Test notification delivery
- [ ] Verify disk space alerts

### Security
- [ ] Verify `.env` file not committed to git
- [ ] Check token files have 600 permissions
- [ ] Review allowed accounts list
- [ ] Document OAuth revocation process

### Documentation
- [ ] Update README with deployment specifics
- [ ] Document any custom configuration
- [ ] Create runbook for common issues
- [ ] Share access instructions with team

### Backup
- [ ] Document backup strategy
- [ ] Test backup restoration
- [ ] Schedule regular backups
- [ ] Store backups securely

## Production Checklist

### Performance
- [ ] Adjust `POLL_INTERVAL` based on usage
- [ ] Configure `MAX_RETRIES` appropriately
- [ ] Set appropriate `LOG_LEVEL` (INFO or WARNING)

### Maintenance
- [ ] Schedule regular updates
- [ ] Monitor disk usage
- [ ] Review logs periodically
- [ ] Test disaster recovery

### User Management
- [ ] Add authorized users to allowlist
- [ ] Document authorization process
- [ ] Create user onboarding guide
- [ ] Plan for access revocation

## Health Checks

### Daily
- [ ] Service running: `docker-compose ps`
- [ ] No errors in logs: `docker-compose logs --tail=50`
- [ ] Disk space adequate: `df -h`

### Weekly
- [ ] Review processing statistics
- [ ] Check notification delivery
- [ ] Verify backups completed
- [ ] Review security logs

### Monthly
- [ ] Update dependencies if needed
- [ ] Review and clean old archives
- [ ] Audit authorized accounts
- [ ] Test disaster recovery

## Troubleshooting

### Service Won't Start
1. Check Docker daemon: `docker info`
2. Check port conflicts: `lsof -i :8080`
3. Review logs: `docker-compose logs`
4. Verify `.env` configuration

### OCR Not Working
1. Test API key: Check Gemini quota
2. Check file format support
3. Review Gemini API logs
4. Verify network connectivity

### Dropbox Issues
1. Check OAuth configuration
2. Verify redirect URI
3. Review allowed accounts
4. Test token refresh

### Notification Issues
1. Verify bot token/credentials
2. Check network connectivity
3. Test API endpoints manually
4. Review notification logs

## Rollback Procedure

If deployment fails:

1. **Stop service**
   ```bash
   docker-compose down
   ```

2. **Restore configuration**
   ```bash
   git checkout .env
   ```

3. **Restore data** (from backup)
   ```bash
   tar -xzf backup.tar.gz
   ```

4. **Rebuild and restart**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## Success Criteria

✅ Service starts without errors  
✅ Test images are processed successfully  
✅ Output files contain correct text  
✅ Original files are archived  
✅ Notifications are delivered (if enabled)  
✅ Logs show normal operation  
✅ No security warnings  
✅ Performance is acceptable  

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Version**: 1.0.0  
**Environment**: [ ] Development [ ] Staging [ ] Production  

---

Notes:
_______________________________________________
_______________________________________________
_______________________________________________
