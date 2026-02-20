import json
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

GITHUB_API = "https://api.github.com"

FONT_SIZE = 18
FONT_SMALL = 16


class GitHubCodespaceManager(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 30
        self.spacing = 20
        self.token = ""
        self.codespaces = []
        self.selected_codespace = None

        self.add_widget(Label(
            text="GitHub Codespace 远程终端",
            size_hint_y=None, height=50,
            font_size=24, bold=True
        ))

        # Token
        self.add_widget(Label(text="GitHub Token", size_hint_y=None, height=40, font_size=FONT_SIZE))
        self.token_input = TextInput(
            password=True, size_hint_y=None, height=60, font_size=FONT_SIZE, padding_x=15
        )
        self.add_widget(self.token_input)

        self.login_btn = Button(
            text="登录并加载 Codespaces", size_hint_y=None, height=60, font_size=FONT_SIZE
        )
        self.login_btn.bind(on_press=self.login_and_load_codespaces)
        self.add_widget(self.login_btn)

        # Codespace 列表
        self.add_widget(Label(text="选择 Codespace", size_hint_y=None, height=40, font_size=FONT_SIZE))
        self.scroll = ScrollView(size_hint_y=0.2)
        self.space_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.space_list.bind(minimum_height=self.space_list.setter('height'))
        self.scroll.add_widget(self.space_list)
        self.add_widget(self.scroll)

        # 命令输入
        self.add_widget(Label(text="执行 Bash 命令", size_hint_y=None, height=40, font_size=FONT_SIZE))
        self.cmd_input = TextInput(
            hint_text="例如：ls, pwd, whoami",
            size_hint_y=None, height=60, font_size=FONT_SIZE, padding_x=15
        )
        self.add_widget(self.cmd_input)

        self.run_btn = Button(
            text="执行命令", size_hint_y=None, height=60, font_size=FONT_SIZE
        )
        self.run_btn.bind(on_press=self.run_bash_and_get_output)
        self.add_widget(self.run_btn)

        # 结果输出
        self.add_widget(Label(text="终端返回结果", size_hint_y=None, height=40, font_size=FONT_SIZE))
        self.result_output = TextInput(
            readonly=True, font_size=FONT_SMALL, size_hint_y=0.4
        )
        self.add_widget(self.result_output)

    def login_and_load_codespaces(self, instance):
        self.token = self.token_input.text.strip()
        if not self.token:
            self.result_output.text = "请输入 Token"
            return

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            r = requests.get(f"{GITHUB_API}/user/codespaces", headers=headers, timeout=15)
            r.raise_for_status()
            self.codespaces = r.json().get("codespaces", [])
            self.update_list()
            self.result_output.text = f"成功加载 {len(self.codespaces)} 个 Codespace"
        except Exception as e:
            self.result_output.text = f"错误：{str(e)}"

    def update_list(self):
        self.space_list.clear_widgets()
        for cs in self.codespaces:
            name = cs.get("display_name", cs["name"])
            btn = Button(
                text=name, size_hint_y=None, height=55,
                background_color=(0.2, 0.6, 1, 1), font_size=FONT_SMALL
            )
            btn.cs = cs
            btn.bind(on_press=self.select_cs)
            self.space_list.add_widget(btn)

    def select_cs(self, instance):
        self.selected_codespace = instance.cs
        self.result_output.text = f"已选中：\n{instance.cs['name']}"

    def run_bash_and_get_output(self, instance):
        if not self.selected_codespace:
            self.result_output.text = "先选中一个 Codespace"
            return

        cmd = self.cmd_input.text.strip()
        if not cmd:
            self.result_output.text = "请输入命令"
            return

        cs_name = self.selected_codespace["name"]
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            sess_url = f"{GITHUB_API}/user/codespaces/{cs_name}/terminals"
            sess_resp = requests.post(sess_url, headers=headers, timeout=10)
            sess_resp.raise_for_status()
            session = sess_resp.json()

            send_url = f"{GITHUB_API}/user/codespaces/{cs_name}/terminals/{session['session_id']}/input"
            requests.post(send_url, headers=headers, data=f"{cmd}\n".encode("utf-8"), timeout=10)

            output_url = f"{GITHUB_API}/user/codespaces/{cs_name}/terminals/{session['session_id']}/output"
            out_resp = requests.get(output_url, headers=headers, timeout=10)
            output = out_resp.json().get("output", "")

            self.result_output.text = f"$ {cmd}\n\n{output}"

        except Exception as e:
            self.result_output.text = f"执行失败：\n{str(e)}"


class CodespaceApp(App):
    def build(self):
        return GitHubCodespaceManager()


if __name__ == "__main__":
    CodespaceApp().run()

