import flet as ft
import asyncio, aiohttp
from typing import Sequence, Optional
from models import Repo, FeaturedEntry, Tweak
import json
import platform

REPOS = [
    "https://raw.githubusercontent.com/Lrdsnow/PureKFDRepo/main/v6/repo.json",
    "https://raw.githubusercontent.com/Lrdsnow/SnowRepo/refs/heads/main/v6/repo.json",
    "http://0.0.0.0:8000/main.json"
]

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
    featured = ft.GridView()

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
    
    def gen_tweak(entry: FeaturedEntry | Tweak, repo_id: int):
        name = ft.Text(entry.name or 'Unknown')
        banner = entry.banner
        load = None
        disabled = True
        if isinstance(entry, FeaturedEntry):
            name.visible = bool(entry.name)
            name.color = entry.fontcolor if entry.fontcolor else name.color
            icon = desc = None
            if getattr(entry.tweak_pair, 'repo', None) and repo_id != None:
                load = tweak_loader(repo_id, entry.tweak_pair)
                disabled = False
        else:
            desc = ft.Text(entry.description, visible=bool(entry.description))
            icon = entry.icon or ft.Icon(ft.icons.QUESTION_MARK)
            if entry.repo and repo_id != None:
                load = tweak_loader(repo_id, entry)
                disabled = False
        return ft.Card(
            ft.Container(
                ft.Column([
                    ft.ListTile(
                        leading=ft.CircleAvatar(foreground_image_src=icon) if isinstance(icon, str) and icon else icon,
                        title=name, subtitle=desc
                    ),
                    ft.Row((ft.FilledButton(text="View", on_click=load, disabled=disabled),), alignment=ft.MainAxisAlignment.END)
                ]),
                image=ft.DecorationImage(banner, fit=ft.ImageFit.COVER, opacity=0.5) if banner else None,
                padding=10,
            ),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    def route_change(route):
        page.views.clear()
        page.add(drawer)
        construct_appbar = lambda title=page.title, **kwargs: ft.AppBar(title=ft.Text(title), bgcolor=ft.colors.SURFACE_VARIANT, **kwargs)
        view_kwargs = lambda title=page.title, **kwargs: {'route': page.route, 'drawer':drawer, 'appbar': construct_appbar(title, **kwargs)}
        match page.route:
            case '/':
                featured.expand = True
                featured.max_extent = 400
                featured.child_aspect_ratio = 2
                page.views.append(ft.View(controls=[featured], **view_kwargs()))
                page.update()
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
                    repo_id, tweak_id = page.route.split(':')[1], page.route.split(':')[-1]
                    try: repo_id = int(repo_id)
                    except:
                        print(f"Invalid repo ID: {repo_id}. Tweak: {tweak_id}")
                        page.route('/')
                        return
                else:
                    repo_id, tweak_id = int(''.join((*filter(str.isdigit, page.route),))), -1
                repo = repos[repo_id]
                tweaks_list = ft.GridView(expand=True, max_extent=400, child_aspect_ratio=2)
                page.views.append(
                    ft.View(controls=[
                        ft.Text(repo.description, theme_style=ft.TextThemeStyle.TITLE_LARGE, visible=bool(repo.description)),
                        tweaks_list,
                    ], **view_kwargs(repo.name))
                )
                page.update()
                for t in repo.packages.values():
                    tweaks_list.controls.append(gen_tweak(t, repo_id))
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
                                    ft.Markdown(tweak.long_description, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB, visible=bool(tweak.long_description)),
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
                
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)
    
    async def get_repo(repo):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(repo) as resp:
                    return Repo.from_json(json.loads(await resp.text()), repo)
        except Exception as e:
            err = f"Invalid repo {repo}: {type(e).__name__}: {e}"
            print(err)
            page.overlay.append(ft.SnackBar(ft.Text(err), open=True))
            page.update()
            return Repo(description=f"Invalid repo {repo}: {type(e).__name__}: {e}")
    
    for repo in REPOS:
        r: Repo = await get_repo(repo)
        repo_id = len(repos)
        repos.append(r)
        drawer.controls.append(ft.NavigationDrawerDestination(label=r.name or "Unknown",
            icon_content=ft.CircleAvatar(foreground_image_src=r.icon) if r.icon else ft.Icon(ft.icons.QUESTION_MARK)))
        drawer.update()

        for entry in r.featured:
            featured.controls.append(gen_tweak(entry, repo_id))
            page.update()

ft.app(main)
