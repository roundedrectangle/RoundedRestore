import flet as ft
import asyncio, aiohttp
from typing import Sequence, Optional
from models import BaseRepo
import json
import platform

REPOS = [
    "https://raw.githubusercontent.com/Lrdsnow/PureKFDRepo/main/v6/repo.json",
    "https://raw.githubusercontent.com/Lrdsnow/SnowRepo/refs/heads/main/v6/repo.json",
]

class Repo(BaseRepo):
    def load(self):
        print("TODO: load")

async def main(page: ft.Page):
    page.title = "RoundedRestore"
    page.theme = ft.Theme(color_scheme_seed=ft.colors.TEAL)

    def handle_change(e: ft.ControlEvent):
        match e.control.selected_index:
            case 0: page.go('/')
            case 1: page.go('/installed')
            case 2: page.go('/settings')
            case _: page.go(f"/repo:{e.control.selected_index - 3}")

    repos: Sequence[Repo] = []

    drawer = ft.NavigationDrawer(
        # on_dismiss=handle_dismissal,
        on_change=handle_change,
        controls=[
            ft.Container(height=12),
            ft.NavigationDrawerDestination(label="Featured", icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME),
            ft.NavigationDrawerDestination(label="Installed", icon=ft.icons.DOWNLOAD_DONE),
            ft.NavigationDrawerDestination(
                icon=ft.icons.SETTINGS_OUTLINED, # icon_content=ft.Icon(ft.icons.YOUR_ICON)
                label="Settings",
                selected_icon=ft.icons.SETTINGS,
            ),
            ft.Divider(thickness=2),
        ],
    )

    def tweak_loader(repo, tweak):
        return lambda _: page.go(f'/tweak:{repo}:{tweak}')

    def route_change(route):
        page.views.clear()
        page.add(drawer)
        construct_appbar = lambda title=page.title, **kwargs: ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.SURFACE_VARIANT, **kwargs)
        view_kwargs = lambda title=page.title, **kwargs: {'route': page.route, 'drawer':drawer, 'appbar': construct_appbar(title, **kwargs)}
        match page.route:
            case '/':
                page.views.append(
                    ft.View(controls=[
                        ft.Text("ETA: never", theme_style=ft.TextThemeStyle.DISPLAY_LARGE)
                    ], **view_kwargs())
                )
            case '/installed':
                page.views.append(
                    ft.View(controls=[
                        ft.ElevatedButton("Coming Never!"),
                    ], **view_kwargs("Installed"))
                )
            case '/settings':
                page.views.append(
                    ft.View(controls=[
                        ft.Text(f'OS: {platform.system()} {platform.release()} {platform.version()}'),
                    ], **view_kwargs("Settings"))
                )
            case page.route if page.route.startswith('/repo') or page.route.startswith('/tweak'):
                if page.route.startswith('/tweak'):
                    repo_id, tweak_id = (int(''.join((*filter(str.isdigit, i),))) for i in page.route.split(':')[-2:])
                else:
                    repo_id, tweak_id = int(''.join((*filter(str.isdigit, page.route),))), -1
                repo = repos[repo_id]
                repos_list = ft.GridView(expand=True, max_extent=400, child_aspect_ratio=2)
                page.views.append(
                    ft.View(controls=[
                        ft.Text(r.description, theme_style=ft.TextThemeStyle.TITLE_LARGE, visible=bool(r.description)),
                        repos_list,
                    ], **view_kwargs(repo.name))
                )
                page.update()
                for i, t in enumerate(repo.packages):
                    repos_list.controls.append(
                        ft.Card(
                            ft.Container(
                                ft.Column([
                                    ft.ListTile(
                                        leading=ft.CircleAvatar(foreground_image_src=t.icon) if t.icon else ft.Icon(ft.icons.QUESTION_MARK),
                                        title=ft.Text(t.name or 'Unknown'),
                                        subtitle=ft.Text(t.description, visible=bool(t.description)),
                                    ),
                                    ft.Row([ft.FilledButton(text="View", on_click=tweak_loader(repo_id, i))], alignment=ft.MainAxisAlignment.END)
                                ]),
                                image=ft.DecorationImage(t.banner, fit=ft.ImageFit.COVER, opacity=0.5) if t.banner else None,
                                padding=10,
                            ),
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        )
                    )
                if page.route.startswith('/tweak'): # /tweak:repoid:tweakid
                    tweak = repos[repo_id].packages[tweak_id]
                    screenshot_list = ft.ListView(expand=True, horizontal=True, spacing=15)
                    page.views.append(
                        ft.View(controls=[
                            ft.Row((
                                ft.Container(ft.Column((
                                    ft.Row([
                                        ft.CircleAvatar(foreground_image_src=tweak.icon),
                                        ft.Text(tweak.author, theme_style=ft.TextThemeStyle.TITLE_SMALL, visible=bool(tweak.author)),
                                        ft.Text(tweak.version, theme_style=ft.TextThemeStyle.TITLE_SMALL, visible=bool(tweak.version)),
                                    ]),
                                    ft.Text(tweak.description, theme_style=ft.TextThemeStyle.TITLE_LARGE, visible=bool(tweak.description)),
                                    ft.Text(tweak.long_description, theme_style=ft.TextThemeStyle.BODY_LARGE, visible=bool(tweak.long_description)),
                                    ft.Row((ft.FilledButton(text="GET"),), alignment=ft.MainAxisAlignment.END),
                                ), expand=True), image=ft.DecorationImage(tweak.banner, fit=ft.ImageFit.COVER, opacity=0.5),
                                expand=True,padding=15),)
                            ), screenshot_list
                        ], **view_kwargs(tweak.name)) # leading...
                    )
                    for s in tweak.screenshots:
                        screenshot_list.controls.append(
                            ft.Image(s, border_radius=ft.border_radius.all(10))
                        )

            case _: page.go('/')
                
        # ListView on repo...
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
    
    async def get_repo(repo):
        async with aiohttp.ClientSession() as session:
            async with session.get(repo) as resp:
                return Repo.from_json(json.loads(await resp.text()), repo)
    
    for repo in REPOS:
        r: Repo = await get_repo(repo)
        repos.append(r)
        drawer.controls.append(ft.NavigationDrawerDestination(label=r.name or "Unknown",
            icon_content=ft.CircleAvatar(foreground_image_src=r.icon) if r.icon else ft.Icon(ft.icons.QUESTION_MARK)))
        drawer.update()

ft.app(main)
