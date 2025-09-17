import random
from datetime import datetime
import re


class TeamProcessor:
    def __init__(self):
        self.teams = []
        self.projects = set()
        self.all_students = set()
        self.valid_teams = []
        self.invalid_teams = []
        self.other_teams = []
        self.unassigned_students = set()

    def process_teams(self, rows):
        # Сначала собираем информацию о всех студентах
        self._collect_students_info(rows)

        # Обрабатываем команды
        self._process_team_data(rows)

        # Дополняем неполные команды
        self._fill_incomplete_teams()

        # Формируем команды из оставшихся студентов
        self._form_teams_from_unassigned()

        # Распределяем проекты
        self._distribute_projects()

        return self._prepare_result()

    def _collect_students_info(self, rows):
        for row in rows:
            # Получаем github-логины всех участников
            github_logins = row.get('github-логины коллег по проекту через запятую', '').split(',')
            for login in github_logins:
                login = re.sub(r'\s+', ' ', login.strip())
                if login:
                    self.all_students.add(login)

    def _process_team_data(self, rows):
        for row in rows:
            team_data = self._parse_team_row(row)

            # github-логины в списке - участники команды
            team_size = len(team_data['team_members'])

            if team_size > 5:
                # Команда с более чем 5 участниками - аннулируется
                self.unassigned_students.update(team_data['team_members'])
                continue

            if team_size < 5:
                # Неполная команда
                team_data['needs_more_students'] = True
                self.invalid_teams.append(team_data)
            else:
                # Полная команда
                if team_data['all_projects_listed']:
                    self.valid_teams.append(team_data)
                else:
                    self.invalid_teams.append(team_data)

    def _parse_team_row(self, row):
        # Получаем github-логины всех участников команды
        github_logins = row.get('github-логины коллег по проекту через запятую', '').split(',')
        team_members = []
        for login in github_logins:
            normalized_login = re.sub(r'\s+', ' ', login.strip())
            if normalized_login:
                team_members.append(normalized_login)

        # Получаем список проектов
        projects_str = row.get('Я хочу работать над проектом...', '')
        projects = []
        if projects_str:
            # Разделяем по различным разделителям и нормализуем
            split_projects = re.split(r'[,\s\t]+', projects_str)
            projects = [re.sub(r'\s+', ' ', p.strip()) for p in split_projects if p.strip()]

        # Проверяем, указаны ли все проекты (условно, что всего их 25)
        all_projects_listed = len(projects) >= 25

        # Получаем время отправки
        submission_time = row.get('Время создания', '')
        try:
            submission_time = datetime.strptime(submission_time, '%Y-%m-%d %H:%M:%S')
        except:
            submission_time = datetime.min

        return {
            'submission_time': submission_time,
            'team_members': team_members,
            'projects': projects,
            'all_projects_listed': all_projects_listed,
            'needs_more_students': False
        }

    def _fill_incomplete_teams(self):
        # Сначала собираем всех неприкаянных студентов
        for team in self.invalid_teams:
            if team['needs_more_students']:
                needed = 5 - len(team['team_members'])
                if needed > 0 and self.unassigned_students:
                    available = min(needed, len(self.unassigned_students))
                    selected = random.sample(list(self.unassigned_students), available)
                    team['team_members'].extend(selected)
                    for s in selected:
                        self.unassigned_students.remove(s)
                    team['needs_more_students'] = len(team['team_members']) < 5

        # Если остались неприкаянные студенты, формируем из них команды
        self._form_teams_from_unassigned()

    def _form_teams_from_unassigned(self):
        # Формируем команды из оставшихся студентов (по 5 человек)
        unassigned_list = list(self.unassigned_students)
        while len(unassigned_list) >= 5:
            team_members = unassigned_list[:5]
            self.other_teams.append({
                'team_members': team_members,
                'projects': [],
                'all_projects_listed': False,
                'needs_more_students': False
            })
            unassigned_list = unassigned_list[5:]

        # Оставшиеся студенты (меньше 5) добавляем в команды, которым не хватает
        for student in unassigned_list:
            for team in self.invalid_teams:
                if team['needs_more_students']:
                    team['team_members'].append(student)
                    if len(team['team_members']) >= 5:
                        team['needs_more_students'] = False
                    break

        # Очищаем список неприкаянных
        self.unassigned_students = set(unassigned_list)

    def _distribute_projects(self):
        # Сначала сортируем валидные команды по времени отправки
        self.valid_teams.sort(key=lambda x: x['submission_time'])

        # Собираем все проекты из всех команд
        all_projects = set()
        for team in self.valid_teams + self.invalid_teams + self.other_teams:
            all_projects.update(team['projects'])

        if not all_projects:
            # Если проекты не указаны, создаем список от 1 до 25
            all_projects = set(str(i) for i in range(1, 26))

        assigned_projects = set()

        # Распределяем проекты среди валидных команд
        for team in self.valid_teams:
            for project in team['projects']:
                if project in all_projects and project not in assigned_projects:
                    team['assigned_project'] = project
                    assigned_projects.add(project)
                    break

        # Оставшиеся проекты распределяем случайным образом среди остальных команд
        remaining_projects = list(all_projects - assigned_projects)
        random.shuffle(remaining_projects)

        all_other_teams = self.invalid_teams + self.other_teams
        for i, team in enumerate(all_other_teams):
            if i < len(remaining_projects):
                team['assigned_project'] = remaining_projects[i]
            else:
                team['assigned_project'] = random.choice(list(all_projects))

    def _prepare_result(self):
        result = {
            'valid_teams': [],
            'invalid_teams': [],
            'other_teams': [],
            'unassigned_students': list(self.unassigned_students)
        }

        for team in self.valid_teams:
            result['valid_teams'].append({
                'team_members': team['team_members'],
                'assigned_project': team.get('assigned_project', 'random'),
                'submission_time': team['submission_time'].strftime('%d.%m.%Y %H:%M:%S')
            })

        for team in self.invalid_teams:
            result['invalid_teams'].append({
                'team_members': team['team_members'],
                'assigned_project': team.get('assigned_project', 'random'),
                'submission_time': team['submission_time'].strftime('%d.%m.%Y %H:%M:%S')
            })

        for team in self.other_teams:
            result['other_teams'].append({
                'team_members': team['team_members'],
                'assigned_project': team.get('assigned_project', 'random')
            })

        return result
