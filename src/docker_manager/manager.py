import subprocess

import docker_manager.docker_response_status as DckStatus

class DockerManager():
	
	def __init__(self, compiled_dir: str) -> None:
		self.compiled_dir = compiled_dir
		
		self.execution_image_name = "informejtycy_checker"
		self.debug_image_name = "informejtycy_debugger"
		
		self.execution_container_name = "informejtycy_checker_container"
		self.debug_container_name = "informejtycy_debugger_container"
	
	def build_for_checker(self, executable_file_name: str) -> tuple[str, bytes]:
		content = f"FROM alpine:latest\n\nCOPY {executable_file_name} {executable_file_name}\n\nRUN apk add libc6-compat\nRUN apk add libstdc++ gcompat\n\nCMD [ \"./{executable_file_name}\" ]"
		
		status = ""
		stdout = bytes()
		
		with open(f"{self.compiled_dir}/dockerfile", "w") as f:
			f.write(content)
		
		try:
			stdout = subprocess.check_output(["docker", "build", "-t", self.execution_image_name, self.compiled_dir])
			status = DckStatus.success
		except:
			status = DckStatus.docker_build_error
		
		return (status, stdout)
	
	def run_for_checker(self, input_: str, memory_limit_MB: int, timeout: int) -> tuple[str, bytes]:
		process = subprocess.Popen(["docker", "run", "-m", f"{memory_limit_MB}m", "--name", self.execution_container_name, self.execution_image_name], stdout=subprocess.PIPE)
		
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
		
		self.stop_docker(process, "informejtycy_checker_container")
		
		return (status, stdout)
	
	def stop_docker(self, process: subprocess.Popen, container_name: str) -> None:
		process.kill()
		# is_running = subprocess.check_output(["docker", "inspect", container_name, "|", "grep", "Running"])
		# is_running = is_running.replace(' ','').replace('\t','').replace('\n','').replace('\r','')
		# print(is_running)
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