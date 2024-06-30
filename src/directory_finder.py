import os

class DirectoryFinder:
    @staticmethod
    def find_java_directories(root_dir):
        java_directories = []
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for file in filenames:
                if file.endswith(".java"):
                    java_directories.append(dirpath)
                    break
        return java_directories