.PHONY: up down seed test demo-rsync demo-pgbackrest compare benchmark report clean logs

up:
	docker compose up -d --build
	@echo "Verifying database readiness and initializing pgBackRest stanza..."
	@sleep 5
	docker compose exec -T db su postgres -c "pgbackrest --stanza=stagepass stanza-create" || echo "[WARN] Stanza create had warnings or stanza exists; proceeding to check..."
	docker compose exec -T db su postgres -c "pgbackrest --stanza=stagepass check"
	python3 scripts/seed_helper.py

seed:
	python3 scripts/seed_helper.py

test:
	APP_URL=http://localhost:8000 DATABASE_URL=postgresql://stagepass:stagepass@localhost:5433/stagepass python3 -m pytest tests/ -v

demo-rsync:
	STAGEPASS_LAB=1 DATABASE_URL=postgresql://stagepass:stagepass@localhost:5433/stagepass APP_URL=http://localhost:8000 python3 scripts/scenario_rsync.py --run-id rsync-run1 --batch rsync-post-snap

demo-pgbackrest:
	STAGEPASS_LAB=1 DATABASE_URL=postgresql://stagepass:stagepass@localhost:5433/stagepass APP_URL=http://localhost:8000 python3 scripts/scenario_pgbackrest.py --run-id pgbackrest-run1 --batch pbr-post-backup

compare:
	python3 scripts/compare.py

benchmark:
	STAGEPASS_LAB=1 DATABASE_URL=postgresql://stagepass:stagepass@localhost:5433/stagepass python3 scripts/benchmark.py --rows 20000 --trials 1 --with-dump

report:
	python3 scripts/compare.py || python scripts/compare.py
	python3 scripts/build_report.py || python scripts/build_report.py
	python3 scripts/build_report_pdf.py || python scripts/build_report_pdf.py
	python3 scripts/build_presentation_template.py || python scripts/build_presentation_template.py

presentation:
	python3 scripts/build_presentation_template.py || python scripts/build_presentation_template.py

pdf-report:
	python3 scripts/build_report_pdf.py || python scripts/build_report_pdf.py


# CAUTION: 'make clean' destroys volumes and recorded result files (CSVs, logs, plots).
# Avoid running during final demo preparation to preserve submission evidence.
clean:
	docker compose down -v || true
	rm -rf results/*.csv results/*.json results/logs/* results/plots/* || true

logs:
	docker compose logs --tail=50 db app
