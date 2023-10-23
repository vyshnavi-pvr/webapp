packer {
  required_plugins {
    amazon = {
      version = ">= 0.0.2"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "source_ami" {
  type    = string
  default = "ami-06db4d78cb1d3bbf9"
}

variable "ssh_username" {
  type    = string
  default = "admin"
}

variable "subnet_id" {
  type    = string
  default = "subnet-09c0777a3452b24b7"
}

variable "ami_user" {
  type    = string
  default = "051986808830"
}

variable "ami_region" {
  type    = string
  default = "us-west-1"
}

source "amazon-ebs" "debian_webapp_ami" {
  ami_name        = "cye6225_${formatdate("YYYY_MM_DD_hh_mm_ss", timestamp())}"
  ami_description = "csye6225 AMI"
  instance_type   = "t2.micro"
  region          = "${var.aws_region}"
  ami_regions = [
    "us-east-1", "${var.ami_region}"
  ]
  ami_users = ["${var.ami_user}"

  aws_polling {
    delay_seconds = 30
    max_attempts  = 50
  }

  source_ami   = "${var.source_ami}"
  ssh_username = "${var.ssh_username}"
  subnet_id    = "${var.subnet_id}"

  launch_block_device_mappings {
    delete_on_termination = true
    device_name           = "/dev/xvda"
    volume_size           = 8
    volume_type           = "gp2"
  }
}

build {
  sources = ["source.amazon-ebs.debian_webapp_ami"]

  provisioner "file" {
    source      = "webapp.zip"
    destination = "~/webapp.zip"
  }

  provisioner "shell" {
    script = "webapp_script.sh"
  }

  provisioner "shell" {
    inline = [
      "export DEBIAN_FRONTEND=noninteractive"
    ]
  }

  // provisioner "shell" {
  //   environment_vars = [
  //     "DEBIAN_FRONTEND=noninteractive",
  //     "CHECKPOINT_DISABLE=1"
  //   ]
  //   inline = [
  //     "sudo apt update -y",
  //     "sudo apt upgrade -y",
  //     "sudo apt install software-properties-common -y",
  //     "sudo apt install python3.11-venv -y",
  //     "python3 -m venv cs_env",
  //     ". cs_env/bin/activate",
  //     "pip install -r requirements.txt"
  //     "sudo apt install postgresql postgresql-contrib -y"
  //   ]
  // }
}
