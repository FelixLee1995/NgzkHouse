import yaml
import sys
import os
import streamlit as st

import sys, getopt
import argparse

def load_yaml(filename):
	if os.path.exists(filename):
		with open(filename, mode="r", encoding="UTF-8") as f:
			data = yaml.load(f, Loader=yaml.FullLoader)
			return data
	return None


class ConfigManager(object):
	def __init__(self):
		###  这里使用 streamlit 网站部署时可以用提供的 secrets来方便的修改， 优选于配置文件的方式

		if 'config_flie' in st.secrets and st.secrets["config_file"] is not None:
			config_file_path = st.secrets["config_flie"]
		else:
			config_file_path = './config.yaml'

		if 'refresh_token' in st.secrets and st.secrets["refresh_token"] is not None:
			refresh_token = st.secrets["refresh_token"]
		if 'refresh_token_s46' in st.secrets and st.secrets["refresh_token_s46"] is not None:
			refresh_token_s46 = st.secrets["refresh_token_s46"]
		if 'refresh_token_h46' in st.secrets and st.secrets["refresh_token_h46"] is not None:
			refresh_token_h46 = st.secrets["refresh_token_h46"]
		else:
			## 如果不采用 streamlit方式的话，  这里应采用配置文件中的
			exit(-10)

		self.config_dict = load_yaml(config_file_path)

		if 'qry_history_spread' in st.secrets and st.secrets["qry_history_spread"] is not None:
			self.config_dict['qry_history_spread'] = int(st.secrets["qry_history_spread"])


		if refresh_token is not None:
			self.config_dict['refresh_token'] = refresh_token

		if refresh_token_s46 is not None:
			self.config_dict['refresh_token_s46'] = refresh_token_s46
		
		if refresh_token_h46 is not None:
			self.config_dict['refresh_token_h46'] = refresh_token_h46

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


