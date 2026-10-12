.PHONY: up down seed test demo-rsync demo-pgbackrest compare benchmark report clean logs

up:
	docker compose up -d --build
	docker compose exec -T db su postgres -c "pgbackrest --stanza=stagepass stanza-create" || true
	python3 scripts/seed_helper.py || true

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
	python3 scripts/compare.py
	python3 scripts/build_report.py
	python3 scripts/build_pptx.py

clean:
	docker compose down -v || true
	rm -rf results/*.csv results/*.json results/logs/* results/plots/* || true

logs:
	docker compose logs --tail=50 db app
