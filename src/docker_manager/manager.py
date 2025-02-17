from __future__ import unicode_literals

import pexpect
import subprocess
from uuid import uuid4

import docker_manager.docker_response_status as DckStatus

class DockerManager():
	
	def __init__(self, compiled_dir: str) -> None:
		self.compiled_dir = compiled_dir
		
		self.execution_image_name = "informejtycy_checker"
	
	'''
	For checker.
	'''

	def build_for_checker(self, executable_file_name: str) -> tuple[str, bytes]:
		content = "\n".join([
			f"# This file was automatically generated by {__name__}",
			f"FROM alpine:latest",
			f"RUN apk add --no-cache libstdc++ libc6-compat",
			f"RUN mkdir app",
			f"RUN addgroup -S appgroup && adduser -S appuser -G appgroup",
			f"COPY {executable_file_name} app/a.out",
			f"RUN chown appuser:appgroup /app/a.out",
			f"RUN chmod 500 /app/a.out",
			f"USER appuser",
			f"CMD [ \"./app/a.out\" ]\n"
		])
		
		status = ""
		stdout = bytes()
		
		with open(f"{self.compiled_dir}/dockerfile", "w") as f:
			f.write(content)
		
		try:
			stdout = subprocess.check_output(["docker", "build", "-t", self.execution_image_name, self.compiled_dir], stderr=subprocess.STDOUT)
			status = DckStatus.success
		except FileNotFoundError:
			status = DckStatus.internal_docker_manager_error
		except:
			status = DckStatus.docker_build_error
		
		return (status, stdout)
	
	def run_for_checker(self, input_: str, memory_limit_MB: int, timeout: int) -> tuple[str, bytes]:
		container_name = str(uuid4())

		process = subprocess.Popen(["docker", "run", "--rm", "--network", "none", "-m", f"{memory_limit_MB}m", "--name", container_name, self.execution_image_name], stdout=subprocess.PIPE)
		
		status = ""
		stdout = bytes()
		try:
			stdout, _ = process.communicate(input=input_, timeout=timeout)
			
			if process.returncode == 137:
				status = DckStatus.memory_limit_exceeded
			elif process.returncode == 0:
				status = DckStatus.success
			else:
				status = DckStatus.runtime_error
		
		except subprocess.TimeoutExpired:
			status = DckStatus.timeout
		except Exception as e:
			status = DckStatus.server_error
		
		process.kill()
		self.stop_container(container_name)
		
		return (status, stdout)
	
	'''
	Additional methods.
	'''

	def stop_container(self, container_name: str) -> None:
		subprocess.run(["docker", "kill", container_name])

	def clear_images(self) -> tuple[str, bytes]:
		status = ""
		stdout = bytes()
		
		try:
			stdout = subprocess.check_output(["docker", "system", "prune"], input='y'.encode('utf-8'))
			status = DckStatus.success
		except Exception as e:
			status = DckStatus.server_error
		
		return (status, stdout)
