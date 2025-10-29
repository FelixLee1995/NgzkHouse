import yaml
import sys
import os
import streamlit as st

def load_yaml(filename):
	if os.path.exists(filename):
		with open(filename, mode="r", encoding="UTF-8") as f:
			data = yaml.load(f, Loader=yaml.FullLoader)
			return data
	return None


class ConfigManager(object):
	def __init__(self):
		###  这里使用 streamlit 网站部署时可以用提供的 secrets来方便的修改， 优选于配置文件的方式

		if 'config_file' in st.secrets and st.secrets["config_file"] is not None:
			config_file_path = st.secrets["config_file"]
		else:
			config_file_path = './config.yaml'

		secrets_dict = dict(st.secrets)


		self.config_dict = load_yaml(config_file_path) | secrets_dict

		print(f"config_dict is {self.config_dict}")
		print(f'type of  st.secrets is {type( st.secrets)}')
		print(f'type of  self.config_dict is {type( self.config_dict)}')





	def get_config(self, key: str, defaultVal):
		if key in self.config_dict and self.config_dict[key] is not None:
			return self.config_dict[key]

		for k, v in self.config_dict.items():
			if k == key and v is not None:
				return v

			if type(v) is dict:
				for k_, v_ in v.items():
					if k_ == key and v_ is not None:
						return v_
		return defaultVal

	def get_var_config(self, key: str, defaultVal):
		if key in self.var_config_dict:
			return self.var_config_dict[key]

		for k, v in self.var_config_dict.items():
			if k == key:
				return v

			if type(v) is dict:
				for k_, v_ in v.items():
					if k_ == key:
						return v_
		return defaultVal


g_config = ConfigManager()


