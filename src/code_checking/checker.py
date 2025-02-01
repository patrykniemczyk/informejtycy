import os
import subprocess
from typing import Callable, Any

from .commands import Compiler
from .pack_loader import PackLoader
from .check_result import CheckResult
import docker_manager.docker_response_status as DckStatus
from docker_manager.manager import DockerManager

class Checker:
	"""
	Main code checking class. Checks everything in check_queue.
	"""
	def __init__(self, compiler: Compiler, pack_loader: PackLoader):
		"""
		:param compiler: Compiler instance
		:param pack_loader: Pack loader instance
		"""
		self.compiler = compiler
		self.pack_loader = pack_loader

		self.compiled_dir = self.compiler.output_dir

		self.check_queue: list[tuple[str, int, str, Callable[[CheckResult, str], None]]] = []
		
		self.docker_manager = DockerManager(self.compiled_dir)
		self.memory_limit_MB = 60

	def push_check(self, filename: str, ex_id: int, auth: str, on_checked_func: Callable[[CheckResult, str], None]) -> None:
		"""
		Push a file to the checking queue.
		:param filename: Name of the file with source code that will be checked.
		:param ex_id: ID of problem, that is being compiled and runned.
		:param auth: User authentication uuid4
		:param on_checked_func: Function to execute when file checking is done.
		"""
		self.check_queue.append((filename, ex_id, auth, on_checked_func))

	def listen(self) -> None:
		"""
		Listens for new files in the checking queue. Should be called in a different thread.
		"""
		while True:
			if len(self.check_queue) > 0:
				filename, ex_id, auth, on_checked = self.check_queue[0]
				result = self.check(filename, ex_id)
				on_checked(result, auth)
				del self.check_queue[0]
				self.docker_manager.clear_images()
				try:
					os.remove(os.path.join(self.compiler.input_dir, filename))
				except:
					pass

	def check(self, code_file: str, ex_id: int) -> CheckResult:
		"""
		Compiles and checks the code file. The file after checking.
		:param code_file: File with source code that needs to be checked.
		:param ex_id: ID of problem, that is being compiled and runned.
		:return: CheckResult class containing results information like
		percent, compilation error etc.
		"""

		score = 0
		result = CheckResult()

		program = self.compiler.compile(code_file)
		
		if not os.path.exists(os.path.join(self.compiled_dir, program)):
			result.compilation_error = True
			return result
		
		status: str = ""
		debuginfo: bytes = bytes()
		status, debuginfo = self.docker_manager.build_for_checker(program)
		
		if status == DckStatus.docker_build_error:
			os.remove(os.path.join(self.compiled_dir, program))
			return result
		
		test_pack = self.pack_loader.load_bytes(ex_id)
		pack_config = self.pack_loader.load_config(ex_id)

		for test_in, test_out in test_pack:
			status, output = self.docker_manager.run_for_checker(input_=test_in.decode("utf-8"), memory_limit_MB=self.memory_limit_MB, timeout=pack_config['time_limit'])#subprocess.check_output(os.path.join(self.compiled_dir, program), input=test_in, timeout=pack_config['time_limit'])
			
			if status == DckStatus.timeout:
				result.time_limit_exceeded = True
			elif status == DckStatus.memory_limit_exceeded:
				result.memory_limit_exceeded = True

			if status == "success" and output.decode()[:-1] == test_out.decode():
				score += 1
			else:
				result.first_failed = test_in.decode("utf-8")
				break

		os.remove(os.path.join(self.compiled_dir, program))
		os.remove(os.path.join(self.compiler.input_dir, code_file))
		result.percentage = (score / len(test_pack)) * 100
		return result